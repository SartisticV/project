// Panzoom setup
document.addEventListener('DOMContentLoaded', function () {
    const mapElement = document.getElementById('map');
    const panzoom = Panzoom(mapElement, {
        maxScale: 5,
        minScale: 0.5,
        contain: 'outside'
    });
    mapElement.addEventListener('wheel', panzoom.zoomWithWheel);

    // Set up tiles for interaction
    const tiles = document.querySelectorAll('.tile');
    tiles.forEach(function (tile) {
        tile.addEventListener('click', function () {
            if (moveInProgress) {
                event.stopPropagation(); // Prevent default click behavior
                return;
            }
            const tileId = tile.getAttribute('data-id');
            const x = tile.getAttribute('data-x');
            const y = tile.getAttribute('data-y');
            const buildings = tile.getAttribute('data-buildings');
            const resources = tile.getAttribute('data-resources');
            const ownerDisplayName = tile.getAttribute('data-display');
            const population = tile.getAttribute('data-population');
            const goods = tile.getAttribute('data-goods')
            const moving_goods = tile.getAttribute('data-moving-goods')
            showTileDetails(tileId, x, y, buildings, resources, goods, moving_goods, ownerDisplayName, population);
        });
    });

    tiles.forEach(function (tile) {
        const owner = tile.getAttribute('data-owner');
        const ownerColor = tile.getAttribute('data-owner-color');
        if (owner) {
            tile.style.border = `2px solid ${hexToRgba(ownerColor, 0.3)}`;
        } else {
            tile.style.border = 'none';
        }
    });

    // Initialize default Tile tab behavior
    selectTab('details');

    // Initialize default User tab behavior
    selectUserTab('info')

    // Load user actions
    loadUserActions();

    // Load user data
    loadUserData()
});

// HELPER FUNCTIONS
// Converts a hex color to rgba format with adjustable transparency (alpha).
function hexToRgba(hex, alpha) {
    hex = hex.replace('#', '');
    const r = parseInt(hex.substring(0, 2), 16);
    const g = parseInt(hex.substring(2, 4), 16);
    const b = parseInt(hex.substring(4, 6), 16);
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

// Retrieve CSRF token from cookie
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

let currentTab = 'details';
// Tab switching logic
function selectTab(tabId) {
    const detailsTabButton = document.querySelector('#details-tab-button');
    const goodsTabButton = document.querySelector('#goods-tab-button');
    const detailsContent = document.querySelector('#details-tab');
    const goodsContent = document.querySelector('#goods-tab');

    if (tabId === 'details') {
        detailsTabButton.classList.add('active-tab');
        goodsTabButton.classList.remove('active-tab');
        detailsContent.style.display = 'block';
        goodsContent.style.display = 'none';
    } else if (tabId === 'goods') {
        detailsTabButton.classList.remove('active-tab');
        goodsTabButton.classList.add('active-tab');
        detailsContent.style.display = 'none';
        goodsContent.style.display = 'block';
    }
    currentTab = tabId;
}

// Show tile details and highlight owned tiles
function showTileDetails(tileId, x, y, buildings, resources, goods, moving_goods, ownerDisplayName, population) {
    // Update the Tile Details tab
    const detailsContent = document.querySelector('#details-tab');
    detailsContent.innerHTML = `
        <h2>Tile Details</h2>
        <p><strong>Position:</strong> (${x}, ${y})</p>
        <p><strong>Buildings:</strong> ${buildings || 'None'}</p>
        <p><strong>Resources:</strong> ${resources || 'None'}</p>
        <p><strong>Population:</strong> ${population || 'None'}</p>
        <p><strong>Owner:</strong> ${ownerDisplayName || 'None'}</p>
    `;

    const tiles = document.querySelectorAll('.tile');
    tiles.forEach(function (tile) {
        const owner = tile.getAttribute('data-owner');
        const ownerColor = tile.getAttribute('data-owner-color');
        if (owner) {
            tile.style.border = `2px solid ${hexToRgba(ownerColor, 0.3)}`;
        }
    });

    const selectedTile = document.querySelector(`[data-id="${tileId}"]`);
    const selectedOwner = selectedTile.getAttribute('data-owner');
    if (selectedOwner !== "None") {
        tiles.forEach(function (tile) {
            const owner = tile.getAttribute('data-owner');
            if (owner && owner === selectedOwner) {
                const ownerColor = tile.getAttribute('data-owner-color');
                tile.style.border = `2px solid ${ownerColor}`;
            }
        });
    }

    showGoodsTab(goods, moving_goods, tileId, x, y); // Populate the Goods tab with current tile's goods
}

function showGoodsTab(goods, moving_goods, tileId, x, y) {
    const goodsList = document.getElementById('goods-tab');
    goods = goods.replace(/'/g, '"'); // Replace single quotes with double quotes for proper JSON parsing

    // Clear existing goods display
    goodsList.innerHTML = '';

    try {
        goods = JSON.parse(goods);
    } catch (error) {
        console.error('Error parsing goods:', error); // Log parsing errors
        goodsList.innerHTML = '<p>No goods in this tile.</p>';
        return;
    }

    // Check if the goods object is empty or all values are 0
    const hasValidGoods = Object.entries(goods).some(([_, quantity]) => quantity > 0);

    // Parse moving_goods if present
    moving_goods = moving_goods.replace(/'/g, '"');
    let movingGoods = {};
    try {
        movingGoods = JSON.parse(moving_goods);
    } catch (error) {
        console.error('Error parsing moving_goods:', error); // Log parsing errors for moving goods
    }

    const hasMovingGoods = Object.values(movingGoods).some(goods => Object.values(goods).some(quantity => quantity > 0));

    // If neither goods nor moving_goods exist, show the "No goods" message
    if ((!goods || Object.keys(goods).length === 0 || !hasValidGoods) && !hasMovingGoods) {
        goodsList.innerHTML = '<p>No goods in this tile.</p>';
        return;
    }

    const csrftoken = getCookie('csrftoken');

    // Validate ownership before rendering Move button
    fetch(`/check_ownership/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken, // Add CSRF token to the headers
        },
        body: JSON.stringify({ tile_id: tileId })
    })
    .then(response => response.json())
    .then(data => {
        // Populate the goods list for goods with quantities > 0
        if (hasValidGoods) {
            for (const [good, quantity] of Object.entries(goods)) {
                if (quantity > 0) {
                    const li = document.createElement('li');
                    li.innerHTML = `${good}: ${quantity}`;
                    if (data.is_owner) {
                        li.innerHTML += `
                            <button onclick="initiateMove('${good}', ${quantity}, ${tileId}, ${x}, ${y})">Move</button>
                        `;
                    }
                    goodsList.appendChild(li);
                }
            }
        }

        // Show moving goods if available
        if (hasMovingGoods) {
            const caravanTitle = document.createElement('h4');
            caravanTitle.textContent = 'Caravans:';
            goodsList.appendChild(caravanTitle);

            for (const [display, items] of Object.entries(movingGoods)) {
                for (const [good, quantity] of Object.entries(items)) {
                    if (quantity > 0) {
                        const li = document.createElement('li');
                        li.innerHTML = `${good}: ${quantity} (${display})`;
                        goodsList.appendChild(li);
                    }
                }
            }
        }
    })
    .catch(error => {
        console.error('Error checking ownership:', error);
        goodsList.innerHTML = '<p>Error verifying ownership. Please try again later.</p>';
    });
}

let currentUserTab = 'info';  // Default tab

// Tab switching logic
function selectUserTab(tabId) {
    const infoTabButton = document.querySelector('#info-tab-button');
    const progressTabButton = document.querySelector('#progress-tab-button');
    const infoContent = document.querySelector('#info-tab');
    const progressContent = document.querySelector('#progress-tab');

    if (tabId === 'info') {
        infoTabButton.classList.add('active-tab');
        progressTabButton.classList.remove('active-tab');
        infoContent.style.display = 'block';
        progressContent.style.display = 'none';
    } else if (tabId === 'progress') {
        infoTabButton.classList.remove('active-tab');
        progressTabButton.classList.add('active-tab');
        infoContent.style.display = 'none';
        progressContent.style.display = 'block';
    }
    currentUserTab = tabId;
}

// Toggle visibility of action sections
function toggleSection(sectionId) {
    const section = document.getElementById(sectionId);
    section.style.display = section.style.display === 'none' ? 'block' : 'none';
}

// Fetch user data and populate actions
function loadUserData() {
    fetch('/get_user_data/')
        .then(response => response.json())
        .then(data => {
            // Display current date
            document.getElementById('current-date').textContent = data.current_date;

            // Render categorized actions
            renderActions('in-progress-list', data.progress, renderProgressActionTemplate);
            renderActions('failed-list', data.failed, renderStatusActionTemplate);
            renderActions('completed-list', data.completed, renderStatusActionTemplate);
        })
        .catch(error => console.error('Error loading user data:', error));
}

// Render list of actions
function renderActions(listId, actions, renderTemplate) {
    const list = document.getElementById(listId);
    list.innerHTML = ''; // Clear existing actions

    if (actions.length === 0) {
        list.innerHTML = '<li>No actions</li>';
    } else {
        actions.forEach(action => {
            const actionItem = document.createElement('li');
            actionItem.innerHTML = renderTemplate(action);
            list.appendChild(actionItem);
        });
    }
}

// Render Progress Action
function renderProgressActionTemplate(action) {
    const { action_type, action_data } = action;

    let actionText = '';
    if (action_type === 'move_goods') {
        const currentTile = action_data.path[action_data.turn - 1];
        actionText = `Move ${action_data.quantity} ${action_data.good} 
                      from (<span class="coordinate" data-xcoor="${action_data.from.x}" data-ycoor="${action_data.from.y}">${action_data.from.x},${action_data.from.y}</span>) 
                      to (<span class="coordinate" data-xcoor="${action_data.to.x}" data-ycoor="${action_data.to.y}">${action_data.to.x},${action_data.to.y}</span>) 
                      for ${action_data.cost} ducats. (<span class="coordinate" data-xcoor="${currentTile.x}" data-ycoor="${currentTile.y}">${action_data.turn}/${action_data.time}</span>)`;
    }

    return `<div class="action-text">${actionText}</div>`;
}

// Render Status Action (Failed/Completed)
function renderStatusActionTemplate(action) {
    const { action_type, action_data, turns_ago } = action;
    const status = action_data.status;

    let actionText = '';
    if (action_type === 'move_goods') {
        const statusText = status.success || status.error;
        const finalTile = status.tile;

        actionText = `Move ${action_data.quantity} ${action_data.good} 
                      from (<span class="coordinate" data-xcoor="${action_data.from.x}" data-ycoor="${action_data.from.y}">${action_data.from.x},${action_data.from.y}</span>) 
                      to (<span class="coordinate" data-xcoor="${action_data.to.x}" data-ycoor="${action_data.to.y}">${action_data.to.x},${action_data.to.y}</span>) - ${statusText}. 
                      Tile: (<span class="coordinate" data-xcoor="${finalTile.x}" data-ycoor="${finalTile.y}">${finalTile.x},${finalTile.y}</span>) 
                      - Completed ${turns_ago} turns ago.`;
    }

    return `<div class="action-text">${actionText}</div>`;
}

let moveFromTile = null;
let moveGood = null;
let moveToTile = null;
let moveInProgress = false; // Flag to check if a move is in progress
let path=[];
let time = 0;
let cost = 0;

// Function to initiate the move
function initiateMove(good, maxQuantity, tileId, x, y) {
    // Disable all Move buttons
    const moveButtons = document.querySelectorAll('button[onclick^="initiateMove"]');
    moveButtons.forEach(button => {
        button.disabled = true;
    });

    moveFromTile = { tileId, x, y }

    // Create input for quantity
    const moveInput = document.createElement('div');
    moveInput.id = 'move-controls';
    moveInput.innerHTML = `
        <label>Amount:</label>
        <input type="number" id="move-quantity" min="1" max="${maxQuantity}" placeholder="Enter amount" onkeyup=enforceMinMax(this)>
        <button id="to-button" onclick="selectMoveFrom('${good}', ${tileId})">To</button>
    `;
    event.target.parentElement.appendChild(moveInput);
}

// Function to start the "Select Destination" phase
function selectMoveFrom(good, tileId) {
    moveGood = { good };
    moveInProgress = true; // Activate move phase

    alert('Select a destination tile to move goods to.');

    // Highlight the current tile in blue
    const currentTile = document.querySelector(`.tile[data-id='${tileId}']`);
    if (currentTile) {
        currentTile.classList.add('highlight-blue');
    }

    const tiles = document.querySelectorAll('.tile');
    tiles.forEach(tile => {
        tile.onclick = function (event) {
            event.stopPropagation(); // Prevent default event bubbling
            const tileId = tile.getAttribute('data-id');
            const x = tile.getAttribute('data-x');
            const y = tile.getAttribute('data-y');
            selectMoveTo(tileId, x, y);
        };
    });
}

// Function to handle selecting the destination tile
function selectMoveTo(tileId, x, y) {
    if (!moveInProgress) return;

    moveToTile = { tileId, x, y };

    // Update quantity input
    const quantity = document.getElementById('move-quantity');
    quantity.addEventListener('input', updateMoveCost);

    // Calculate path
    calculatePath(moveFromTile.x, moveFromTile.y, x, y).then(result => {
        if (result) {
            path = result.path;
            time = result.time;

            cost = parseInt(quantity.value) * time

            // Reset previous highlights and numbers
            document.querySelectorAll('.tile').forEach(tile => {
                tile.classList.remove('highlight-red', 'highlight-white');
                const span = tile.querySelector('span');
                if (span) span.remove(); // Remove old numbers
            });

            // Highlight the path tiles in white and number them
            path.forEach((tileInfo, index) => {
                const pathTile = document.querySelector(`.tile[data-id='${tileInfo.tileId}']`);
                if (pathTile) {
                    pathTile.classList.add('highlight-white');
                    // Add a number inside the tile
                    const numberLabel = document.createElement('span');
                    numberLabel.textContent = index+1;
                    pathTile.appendChild(numberLabel); // Insert into tile
                }
            });

            // Highlight the destination tile in red
            const selectedTile = document.querySelector(`.tile[data-id='${tileId}']`);
            if (selectedTile) {
                selectedTile.classList.add('highlight-red');
            }

            // Update the "To" button with the selected tile's coordinates
            const moveCost = document.getElementById('move-cost');
            if (moveCost) {
                moveCost.textContent = `${cost.toFixed(2)}`;
            } else {
                const toButton = document.getElementById('to-button');
                if (toButton) {
                    toButton.outerHTML = `<label>Cost:</label><span id="move-cost">${cost.toFixed(2)}</span>`;
                }
            }

            // Add the confirm button next to the input field
            const moveControls = document.getElementById('move-controls');
            if (moveControls && !document.getElementById('confirm-move-btn')) {
                const confirmButton = document.createElement('button');
                confirmButton.id = 'confirm-move-btn';
                confirmButton.textContent = 'Confirm';
                confirmButton.onclick = confirmMove;
                moveControls.appendChild(confirmButton);
            }
        }
    }).catch(error => {
        console.error('Error calculating path:', error);
        alert('An error occurred while calculating the path.');
    });
}

// Function to confirm and queue the move action
function confirmMove() {
    const quantity = document.getElementById('move-quantity').value;
    cost = parseInt(quantity)*time;

    if (!quantity || quantity < 1) {
        alert('Please enter a valid quantity.');
        return;
    }

    fetch('/queue_action/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            action_type: 'move_goods',
            details: {
                good: moveGood.good,
                quantity: parseInt(quantity),
                from: moveFromTile,
                to: moveToTile,
                path: path,
                time: time,
                cost: cost,
            },
        }),
    }).then(response => {
        if (response.ok) {
            alert('Action queued successfully!');
            resetMoveState();
            loadUserActions()
        } else {
            alert('Failed to queue action. Please try again.');
        }
    }).catch(error => {
        console.error('Error:', error);
        alert('An error occurred. Please try again.');
    });
}

// Reset the move state and restore onclick handlers
function resetMoveState() {
    moveInProgress = false; // Deactivate move phase

    // Remove highlights
    document.querySelectorAll('.tile').forEach(tile => {
        tile.classList.remove('highlight-blue', 'highlight-red', 'highlight-white');

        const span = tile.querySelector('span');
        if (span) span.remove(); // Remove old numbers

        // Remove custom JavaScript onclick handler
        tile.onclick = null;
    });

    // Re-enable all Move buttons
    const moveButtons = document.querySelectorAll('button[onclick^="initiateMove"]');
    moveButtons.forEach(button => {
        button.disabled = false;
    });

    // Remove the confirm button and associated controls
    const moveControls = document.getElementById('move-controls');
    if (moveControls) {
        moveControls.remove();
    }

    // Clear state variables
    moveFromTile = null;
    moveToTile = null;
}

// ACTION LOGIC
function loadUserActions() {
    fetch('/get_user_actions/')
        .then(response => response.json())
        .then(data => {
            const actionList = document.getElementById('action-list');
            actionList.innerHTML = '';

            if (data.actions.length === 0) {
                actionList.innerHTML = '<li>No actions</li>';
            } else {
                data.actions.forEach(action => {
                    const actionItem = document.createElement('li');
                    actionItem.innerHTML = renderActionTemplate(action);
                    actionList.appendChild(actionItem);
                });
            }
        })
        .catch(error => console.error('Error loading user actions:', error));
}

function renderActionTemplate(action) {
    const { id, action_type, action_data } = action;

    let actionText = '';
    if (action_type === 'move_goods') {
        // Create the action text
        actionText = `Move ${action_data.quantity} ${action_data.good} 
                      from (<span class="coordinate" data-xcoor="${action_data.from.x}" data-ycoor="${action_data.from.y}">${action_data.from.x},${action_data.from.y}</span>) 
                      to (<span class="coordinate" data-xcoor="${action_data.to.x}" data-ycoor="${action_data.to.y}">${action_data.to.x},${action_data.to.y}</span>) 
                      for ${action_data.cost} ducats.`;
    }

    return `
        ${actionText}
        <button onclick="removeAction(${id})">Remove</button>
    `;
}

// Event listener for hover actions
document.addEventListener('mouseover', function (event) {
    if (event.target && event.target.classList.contains('coordinate')) {
        const x = event.target.getAttribute('data-xcoor');
        const y = event.target.getAttribute('data-ycoor');
        highlightTile(x, y);
    }
});

document.addEventListener('mouseout', function (event) {
    if (event.target && event.target.classList.contains('coordinate')) {
        const x = event.target.getAttribute('data-xcoor');
        const y = event.target.getAttribute('data-ycoor');
        removeHighlightTile(x, y);
    }
});

// Highlight the tile corresponding to the coordinates
function highlightTile(x, y) {
    const tile = document.querySelector(`.tile[data-x="${x}"][data-y="${y}"]`);
    if (tile) {
        tile.classList.add('highlight-yellow');
    }
}

// Remove the highlight from the tile
function removeHighlightTile(x, y) {
    const tile = document.querySelector(`.tile[data-x="${x}"][data-y="${y}"]`);
    if (tile) {
        tile.classList.remove('highlight-yellow');
    }
}

function removeAction(actionId) {
    const csrftoken = getCookie('csrftoken');
    fetch(`/remove_action/${actionId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrftoken, // CSRF token
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Action removed successfully!');
            loadUserActions(); // Refresh the action list
        } else {
            alert('Failed to remove action: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error removing action:', error);
        alert('An error occurred while removing the action.');
    });
}


// Tooltip handlers
function showTooltip(event, tileId, x, y, buildings, resources, display, population) {
    const tooltip = document.getElementById("tooltip");
    tooltip.style.display = 'block';
    tooltip.style.left = event.pageX + 10 + 'px';
    tooltip.style.top = event.pageY + 10 + 'px';
    tooltip.innerHTML = `
        <strong>(${x}, ${y})</strong><br>
        <small>Buildings: ${buildings || 'None'}</small><br>
        <small>Resources: ${resources || 'None'}</small><br>
        <small>Population: ${population || 'None'}</small><br>
        <small>Owner: ${display || 'None'}</small>
    `;
}

function hideTooltip() {
    const tooltip = document.getElementById("tooltip");
    tooltip.style.display = 'none';
}


function calculatePath(startX, startY, goalX, goalY, speed = 2) {
    return new Promise((resolve, reject) => {
        fetch(`/calculate_path/?start_x=${startX}&start_y=${startY}&goal_x=${goalX}&goal_y=${goalY}&speed=${speed}`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    resolve({ path: data.path, time: data.time });
                } else {
                    alert('Error calculating path: ' + data.error);
                    reject('Error calculating path');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred while calculating the path.');
                reject(error);
            });
    });
}

// Function to update the move cost when the quantity input changes
function updateMoveCost() {
    const quantity = document.getElementById('move-quantity').value || 0;

    // Calculate cost
    const cost = quantity*time

    // Update the move cost display
    const moveCostSpan = document.getElementById('move-cost');
    if (moveCostSpan) {
        moveCostSpan.textContent = `${cost.toFixed(2)}`;
    }
}

// Input values enforcer
function enforceMinMax(el) {
  if (el.value != "") {
    if (parseInt(el.value) < parseInt(el.min)) {
      el.value = el.min;
    }
    if (parseInt(el.value) > parseInt(el.max)) {
      el.value = el.max;
    }
  }
  // Update moving cost to enforce min/max values
  if(moveToTile) {
      updateMoveCost();
  }
}