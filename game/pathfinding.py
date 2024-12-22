from heapq import heappush, heappop
from math import inf

TERRAIN_COSTS = {
    'plains': 1,
    'mountains': 2,
    'water': 4,
    'fields': 1,
    'forest': 2,
    'city': 1,
}

def chebyshev_distance(start, goal):
    """Calculate Chebyshev distance between two points."""
    return max(abs(start[0] - goal[0]), abs(start[1] - goal[1]))

def find_path(start, goal, terrain_data, tile_mapping, speed=2):
    """
    Find the path using A* and calculate movement costs dynamically.

    Args:
        start: Tuple (x, y) of start position.
        goal: Tuple (x, y) of goal position.
        terrain_data: Dictionary mapping (x, y) -> terrain type.
        tile_mapping: Dictionary mapping (x, y) -> tileId.
        speed: Movement budget per turn.

    Returns:
        A tuple (formatted_path, cost) where formatted_path is a list of tile dictionaries,
        and cost is the monetary cost based on the length of the path.
    """
    # Handle adjacent tiles directly
    if chebyshev_distance(start, goal) == 1:
        return [{"tileId": tile_mapping[goal], "x": goal[0], "y": goal[1]}], TERRAIN_COSTS[terrain_data[goal]]

    # A* algorithm setup
    open_set = []
    heappush(open_set, (0, start))
    came_from = {}
    g_score = {start: 0}

    while open_set:
        _, current = heappop(open_set)

        if current == goal:
            break

        # Generate all 8 possible neighbors (diagonal + orthogonal)
        neighbors = [
            (current[0] + dx, current[1] + dy)
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
        ]

        for neighbor in neighbors:
            if neighbor not in terrain_data:
                continue  # Ignore out-of-bound tiles.

            terrain = terrain_data[neighbor]
            terrain_cost = TERRAIN_COSTS.get(terrain, inf)

            # Calculate the g_score
            tentative_g_score = g_score[current] + terrain_cost

            if tentative_g_score < g_score.get(neighbor, inf):
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g_score
                heappush(open_set, (g_score[neighbor] + chebyshev_distance(neighbor, goal), neighbor))

    # Reconstruct path
    path = []
    current = goal
    while current in came_from:
        path.append(current)
        current = came_from[current]
    path.reverse()

    # Calculate speed intervals
    interval_path = []
    cost = 0
    current_speed = 0
    for tile in path:
        terrain_cost = TERRAIN_COSTS[terrain_data[tile]]
        current_speed += terrain_cost

        if current_speed >= speed:
            interval_path.append(tile)
            current_speed = 0
        cost += terrain_cost

    # Ensure the goal is always included
    if not interval_path or interval_path[-1] != goal:
        interval_path.append(goal)

    # Format path with tileId, x, and y
    formatted_path = [
        {"tileId": tile_mapping[tile], "x": tile[0], "y": tile[1]}
        for tile in interval_path
    ]

    return formatted_path, len(interval_path)
