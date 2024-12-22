document.addEventListener('DOMContentLoaded', () => {
    const addButton = document.getElementById('add-good');
    const goodsContainer = document.getElementById('goods-container');
    const hiddenGoodsInput = document.getElementById('id_goods'); // Default input field for goods

    if (!goodsContainer) return;

    // Initialize goods object from the hidden input field
    let goods = {};
    if (hiddenGoodsInput) {
        try {
            goods = JSON.parse(hiddenGoodsInput.value);
            for (const [key, value] of Object.entries(goods)) {
                addGoodRow(key, value);
            }
        } catch (e) {
            console.error("Failed to parse goods JSON:", e);
            goods = {};  // Reset goods in case of error
        }
    }

    addButton.addEventListener('click', () => {
        event.preventDefault(); // Prevents the form from submitting
        const goodNameInput = document.getElementById('good-name');
        const goodAmountInput = document.getElementById('good-amount');

        const goodName = goodNameInput.value.trim();
        const goodAmount = parseInt(goodAmountInput.value, 10);

        if (!goodName || isNaN(goodAmount)) {

            alert(`goodName: "${goodName}", goodAmount: "${goodAmount}"`);
            return;
        }

        if (!(goodName in goods)) {
            goods[goodName] = goodAmount;
            addGoodRow(goodName, goodAmount);
            updateHiddenGoodsInput();
        } else {
            alert("This good already exists!");
        }

        goodNameInput.value = '';
        goodAmountInput.value = '';
    });

    // Add a row for a new good
    function addGoodRow(name, amount) {
        const row = document.createElement('div');
        row.innerHTML = `
            <label>${name}: </label>
            <input type="number" value="${amount}" min="0" data-good="${name}">
            <button type="button" data-good="${name}" class="remove-good">Remove</button>
        `;
        goodsContainer.appendChild(row);

        // Handle changes in amount
        row.querySelector('input').addEventListener('change', (e) => {
            goods[name] = parseInt(e.target.value, 10) || 0;
            updateHiddenGoodsInput();
        });

        // Handle removing a good
        row.querySelector('.remove-good').addEventListener('click', () => {
            delete goods[name];
            row.remove();
            updateHiddenGoodsInput();
        });
    }

    // Update the hidden input field with the current goods object
    function updateHiddenGoodsInput() {
        hiddenGoodsInput.value = JSON.stringify(goods);
    }
});

