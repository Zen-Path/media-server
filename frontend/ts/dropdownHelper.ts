/**
 * Creates the ellipsis trigger button.
 */
export function createMenuTrigger(actions) {
    const container = document.createElement("div");
    container.className = "dropdown";

    const btn = document.createElement("button");
    btn.className = "action-btn";
    btn.innerHTML = `<i class="fa-solid fa-ellipsis-vertical"></i>`;

    const menu = renderDropdownMenu(actions, btn);
    container.append(btn, menu);

    btn.onclick = (e) => {
        e.stopPropagation();

        menu.togglePopover();
    };

    container.appendChild(btn);
    return container;
}

/**
 * Generates the actual dropdown HTML on demand.
 */
function renderDropdownMenu(actions: any[], anchorBtn: HTMLButtonElement) {
    const menu = document.createElement("div");
    menu.setAttribute("popover", "auto");
    menu.className = "dropdown-content";

    // Position the menu whenever it opens
    menu.addEventListener("toggle", (event) => {
        if (event.newState === "open") {
            const rect = anchorBtn.getBoundingClientRect();
            menu.style.margin = "0";
            menu.style.inset = "auto";

            // menu.style.position = "fixed";
            menu.style.top = `${rect.bottom}px`;
            menu.style.left = `${rect.left}px`;

            // 3. Prevent the menu from going off-screen on the right
            const menuRect = menu.getBoundingClientRect();
            if (rect.left + menuRect.width > window.innerWidth) {
                menu.style.left = `${rect.right - menuRect.width}px`;
            }
        }
    });

    actions.forEach((action) => {
        const btn = document.createElement("button");
        btn.className = `menu-item`;

        const iconEl = document.createElement("i");
        iconEl.className = `fa-solid ${action.icon} ${action.className || ""}`;

        const labelEl = document.createElement("span");
        labelEl.textContent = action.label;

        btn.append(iconEl, labelEl);

        btn.onclick = async (e) => {
            e.stopPropagation();

            await action.onClick();
            menu.hidePopover();
        };

        menu.appendChild(btn);
    });

    return menu;
}
