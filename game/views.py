from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import logout
from django.contrib.admin.views.decorators import staff_member_required
from .models import Tile, QueuedAction, ProgressAction, StatusAction, GameDate
from .pathfinding import find_path
from django.db import models
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from datetime import timedelta


@login_required
def map_view(request):
    user = request.user
    tiles = Tile.objects.all()

    # Calculate population for user's owned tiles
    user_population = tiles.filter(owner=user).aggregate(total_population=models.Sum('population'))[
                          'total_population'] or 0

    # Get user's money
    money = user.profile.money

    # Get user's display name
    display_name = user.profile.display_name

    return render(request, 'map.html', {
        'tiles': tiles,
        'user_population': user_population,
        'money': money,
        'display_name':display_name
    })

@login_required
def check_ownership(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            tile_id = data.get('tile_id')
            tile = Tile.objects.get(id=tile_id)

            # Check if the current user owns the tile
            is_owner = tile.owner == request.user
            return JsonResponse({'is_owner': is_owner})

        except Tile.DoesNotExist:
            return JsonResponse({'is_owner': False}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@csrf_exempt
def queue_action(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        action = QueuedAction.objects.create(
            user=request.user,
            action_type=data['action_type'],
            details=data['details']
        )
        return JsonResponse({'success': True, 'action_id': action.id})
    return JsonResponse({'success': False}, status=400)

@login_required
def remove_action(request, action_id):
    if request.method == 'POST':  # Ensure it's a POST request
        try:
            action = QueuedAction.objects.get(id=action_id, user=request.user)
            action.delete()
            return JsonResponse({'success': True})
        except QueuedAction.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Action not found.'})
    return JsonResponse({'success': False, 'error': 'Invalid request method.'})


@login_required
def get_user_actions(request):
    actions = QueuedAction.objects.filter(user=request.user).order_by('timestamp')
    action_list = [
        {
            'id': action.id,
            'action_type': action.action_type,
            'action_data': action.details,
        }
        for action in actions
    ]
    return JsonResponse({'actions': action_list})

@login_required
def get_user_data(request):
    # Fetch the current game date
    game_date = GameDate.objects.first()

    # Fetch all actions
    progress_actions = ProgressAction.objects.filter(user=request.user)
    status_actions = StatusAction.objects.filter(user=request.user)

    # Organize actions into categories
    progress = []
    failed = []
    completed = []

    # Handle Progress Actions
    for action in progress_actions:
        progress.append({
            'id': action.id,
            'action_type': action.action_type,
            'action_data': action.details,
        })

    # Handle Status Actions
    for action in status_actions:
        # Determine if it’s failed or completed
        status = action.details.get('status', {})
        status_type = 'failed' if 'error' in status else 'completed'

        formatted_action = {
            'id': action.id,
            'action_type': action.action_type,
            'action_data': action.details,
            'turns_ago': (game_date.current_date - action.completion_date).days,
        }

        if status_type == 'failed':
            failed.append(formatted_action)
        else:
            completed.append(formatted_action)

    # Return data as JSON
    return JsonResponse({
        'current_date': game_date.current_date.strftime('%B %d, %Y'),
        'progress': progress,
        'failed': failed,
        'completed': completed,
    })


@staff_member_required
def resolve_actions(request):
    if request.method == 'POST':
        # Retrieve the game date
        game_date = GameDate.objects.first()
        if not game_date:
            game_date = GameDate.objects.create()  # Initialize if missing

        # Handle queued actions
        actions = QueuedAction.objects.all()
        print(f"Processing {actions.count()} actions...")
        for action in actions:
            print(f"Resolving action: {action.id}, Type: {action.action_type}")
            if action.action_type == 'move_goods':
                details = action.details
                from_tile = Tile.objects.get(id=details['from']['tileId'])
                good = details['good']
                quantity = details['quantity']
                cost = details['cost']
                user = action.user

                # Check conditions: enough goods and money
                if from_tile.goods.get(good, 0) < quantity:
                    StatusAction.objects.create(
                        user=user,
                        action_type='move_goods',
                        details={**details, "status": {"error": "not enough goods", "tile": {"x": from_tile.x, "y": from_tile.y}}},
                        completion_date=game_date.current_date
                    )
                    continue

                if user.profile.money < cost:
                    StatusAction.objects.create(
                        user=user,
                        action_type='move_goods',
                        details={**details, "status": {"error": "not enough money", "tile": {"x": from_tile.x, "y": from_tile.y}}},
                        completion_date=game_date.current_date
                    )
                    continue

                # Deduct resources and money
                from_tile.goods[good] -= quantity
                from_tile.save()
                user.profile.money -= cost
                user.profile.save()

                # Add action to ProgressAction
                ProgressAction.objects.create(
                    user=user,
                    action_type='move_goods',
                    details={**details, "turn": 0}  # Start with turn 0
                )

        # Clear processed queued actions
        actions.delete()

        # Handle progress actions
        progress_actions = ProgressAction.objects.all()
        print(f"Progressing {progress_actions.count()} actions...")

        for progress in progress_actions:
            print(f"Advancing action: {progress.id}, Type: {progress.action_type}")
            details = progress.details
            turn = details['turn']
            path = details['path']
            good = details['good']
            quantity = details['quantity']
            time = details['time']
            user = progress.user
            display_name = user.profile.display_name

            # Get current and previous tiles
            current_tile_data = path[turn]
            current_tile = Tile.objects.get(id=current_tile_data['tileId'])

            if turn > 0:  # Remove from previous tile's moving_goods
                prev_tile_data = path[turn - 1]
                prev_tile = Tile.objects.get(id=prev_tile_data['tileId'])

                # Update moving_goods in the previous tile for the specific user
                if prev_tile.moving_goods.get(display_name, {}).get(good, 0) < quantity:
                    StatusAction.objects.create(
                        user=user,
                        action_type='move_goods',
                        details={**details, "status": {"error": f"goods were lost", "tile": {"x": prev_tile.x, "y": prev_tile.y}}},
                        completion_date=game_date.current_date
                    )
                    progress.delete()
                    continue
                else:
                    prev_tile.moving_goods[display_name][good] = prev_tile.moving_goods.get(display_name, {}).get(good, 0) - quantity
                    prev_tile.save()

            # Add to current tile's moving_goods for the specific user
            if display_name not in current_tile.moving_goods:
                current_tile.moving_goods[display_name] = {}

            current_tile.moving_goods[display_name][good] = current_tile.moving_goods[display_name].get(good, 0) + quantity
            current_tile.save()

            # Move forward
            progress.details['turn'] += 1
            progress.save()

            # If action is complete
            if progress.details['turn'] >= time:
                # Transfer goods to destination
                current_tile.goods[good] = current_tile.goods.get(good, 0) + quantity

                # Remove from current tile's moving_goods
                current_tile.moving_goods[display_name][good] -= quantity
                if current_tile.moving_goods[display_name][good] <= 0:
                    del current_tile.moving_goods[display_name][good]

                current_tile.save()

                # Mark as completed
                StatusAction.objects.create(
                    user=progress.user,
                    action_type='move_goods',
                    details={**details, "status": {"success": "goods moved successfully", "tile": {"x": current_tile.x, "y": current_tile.y}}},
                    completion_date=game_date.current_date
                )

                # Remove completed progress action
                progress.delete()

        # Increment the date (simulate end turn)
        game_date.current_date += timedelta(days=1)
        game_date.save()

        # Optionally, add logic here for logging out users except admins
        if request.POST.get('end_turn', False):  # Check if it's the end turn action
            log_out_users()

        # Redirect back to admin
        return redirect('admin:index')
    return JsonResponse({'error': 'Invalid request method'}, status=400)

def log_out_users():
    """
    Logs out all users except for staff/admin users.
    """
    users = User.objects.exclude(is_staff=True)  # Get all users except staff/admin
    for user in users:
        logout(user)


def get_terrain_and_tile_data(tiles):
    """Fetch terrain and tile data for a batch of tiles."""
    query = Tile.objects.filter(
        x__in=[t[0] for t in tiles],
        y__in=[t[1] for t in tiles]
    )
    terrain_data = {}
    tile_mapping = {}

    for tile in query:
        terrain_data[(tile.x, tile.y)] = tile.terrain
        tile_mapping[(tile.x, tile.y)] = tile.id

    return terrain_data, tile_mapping

def calculate_path(request):
    """API to calculate the path and return the intervals and cost."""
    try:
        start = (int(request.GET['start_x']), int(request.GET['start_y']))
        goal = (int(request.GET['goal_x']), int(request.GET['goal_y']))
        speed = int(request.GET.get('speed', 4))

        # Fetch all tiles within the bounding box of start and goal
        min_x = min(start[0], goal[0]) - 1
        max_x = max(start[0], goal[0]) + 1
        min_y = min(start[1], goal[1]) - 1
        max_y = max(start[1], goal[1]) + 1

        tiles = [(x, y) for x in range(min_x, max_x + 1) for y in range(min_y, max_y + 1)]
        terrain_data, tile_mapping = get_terrain_and_tile_data(tiles)

        # Perform pathfinding
        path, time = find_path(start, goal, terrain_data, tile_mapping, speed)

        return JsonResponse({'success': True, 'path': path, 'time': time})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
