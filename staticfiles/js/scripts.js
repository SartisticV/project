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
            const tileId = tile.getAttribute('data-id');
            const x = tile.getAttribute('data-x');
            const y = tile.getAttribute('data-y');
            const buildings = tile.getAttribute('data-buildings');
            const resources = tile.getAttribute('data-resources');
            const ownerDisplayName = tile.getAttribute('data-display');
            const population = tile.getAttribute('data-population');
            const goods = tile.getAttribute('data-goods')
            showTileDetails(tileId, x, y, buildings, resources, goods, ownerDisplayName, population);
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

    // Initialize default tab behavior
    selectTab('details');
});

// Converts a hex color to rgba format with adjustable transparency (alpha).
function hexToRgba(hex, alpha) {
    hex = hex.replace('#', '');
    const r = parseInt(hex.substring(0, 2), 16);
    const g = parseInt(hex.substring(2, 4), 16);
    const b = parseInt(hex.substring(4, 6), 16);
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
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
function showTileDetails(tileId, x, y, buildings, resources, goods, ownerDisplayName, population) {
    const activeTab = document.querySelector('.active-tab').id; // Get the currently active tab

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

    // Update the Goods tab (if it's active, or regardless of active tab)
    showGoodsTab(goods);

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

    showGoodsTab(goods); // Populate the Goods tab with current tile's goods
}

// Goods movement logic
let moveFromTile = null;
let moveToTile = null;

function showGoodsTab(goods) {
    const goodsList = document.getElementById('goods-tab');

    // Clear existing goods display
    goodsList.innerHTML = '';

    // Check if goods are null or empty
    if (!goods || goods === 'null') {
        goodsList.innerHTML = '<p>No goods in this tile.</p>';
        return;
    }

    // Try parsing goods only if it's a valid JSON string (not empty or null)
    if (typeof goods === 'string') {
        try {
            goods = JSON.parse(goods);
        } catch (error) {
            goodsList.innerHTML = '<p>No goods in this tile.</p>';
            return;
        }
    }

    // Check if the parsed goods object is empty
    if (Object.keys(goods).length === 0) {
        goodsList.innerHTML = '<p>No goods in this tile.</p>';
        return;
    }

    // Populate the goods list if available
    for (const [good, quantity] of Object.entries(parsedGoods)) {
        const li = document.createElement('li');
        li.innerHTML = `
            ${good}: ${quantity}
            <button onclick="initiateMove('${good}', ${quantity})">Move</button>
        `;
        goodsList.appendChild(li);
    }
}



function initiateMove(good, maxQuantity) {
    const moveInput = document.createElement('div');
    moveInput.innerHTML = `
        <input type="number" id="move-quantity" min="1" max="${maxQuantity}" placeholder="Enter amount">
        <button onclick="selectMoveFrom('${good}')">To</button>
    `;
    event.target.parentElement.appendChild(moveInput);
}

function selectMoveFrom(good) {
    moveFromTile = { good };
    alert('Select a destination tile to move goods to.');
}

function selectMoveTo(tileId, x, y) {
    moveToTile = { tileId, x, y };
    alert(`Selected move destination: (${x}, ${y}).`);
    document.getElementById('goods-list').innerHTML += `
        <button onclick="confirmMove()">Confirm</button>
    `;
}

function confirmMove() {
    const quantity = document.getElementById('move-quantity').value;
    if (!quantity || quantity < 1) {
        alert('Please enter a valid quantity.');
        return;
    }
    // Store the action directly via POST fetch
    fetch('/queue_action/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            action_type: 'move_goods',
            details: {
                good: moveFromTile.good,
                quantity: parseInt(quantity),
                from: moveFromTile,
                to: moveToTile,
            },
        }),
    }).then(response => {
        if (response.ok) {
            alert('Action queued successfully!');
            document.querySelectorAll('.tile').forEach(tile => tile.classList.remove('highlight-blue', 'highlight-red'));
        }
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
