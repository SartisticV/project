from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from .models import Tile, QueuedAction
from django.db import models
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json


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


@staff_member_required
def resolve_actions(request):
    if request.method == 'POST':  # Only allow POST requests to prevent accidental resolution
        actions = QueuedAction.objects.all()
        for action in actions:
            if action.action_type == 'move_goods':
                from_tile = Tile.objects.get(id=action.details['from'])
                to_tile = Tile.objects.get(id=action.details['to'])
                good = action.details['good']
                quantity = action.details['quantity']

                # Perform the move if enough goods exist
                if from_tile.goods.get(good, 0) >= quantity:
                    from_tile.goods[good] -= quantity
                    to_tile.goods[good] = to_tile.goods.get(good, 0) + quantity
                    from_tile.save()
                    to_tile.save()

        # Delete resolved actions
        actions.delete()

        if request.is_ajax():
            return JsonResponse({'success': True})
        return redirect('admin:index')  # Redirect to the admin panel
    return JsonResponse({'error': 'Invalid request method'}, status=400)
