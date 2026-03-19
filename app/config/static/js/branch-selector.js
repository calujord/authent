// Branch selector functionality
(function () {
    'use strict';

    // Función para crear el selector de sucursales
    function createBranchSelector() {
        // Buscar el contenedor del sidebar
        const sidebar = document.querySelector('[data-unfold-sidebar]');
        if (!sidebar) return;

        // Buscar el search input
        const searchContainer = sidebar.querySelector('.relative');
        if (!searchContainer) return;

        // Crear el contenedor del selector
        const selectorContainer = document.createElement('div');
        selectorContainer.className = 'px-4 py-3 border-b border-gray-200 dark:border-gray-700';
        selectorContainer.innerHTML = `
            <label for="branch-selector" class="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-2">
                Sucursal Activa
            </label>
            <select 
                id="branch-selector" 
                class="w-full px-3 py-2 text-sm bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 text-gray-900 dark:text-gray-100"
            >
                <option value="">Seleccionar sucursal...</option>
            </select>
        `;

        // Insertar después del search
        searchContainer.parentNode.insertBefore(selectorContainer, searchContainer.nextSibling);

        // Obtener el select
        const select = selectorContainer.querySelector('#branch-selector');

        // Cargar las sucursales del usuario desde el atributo data
        const branches = window.userBranches || [];
        const activeBranchId = window.activeBranchId;

        // Poblar el select con las sucursales
        branches.forEach(membership => {
            const option = document.createElement('option');
            option.value = membership.branch.id;
            option.textContent = `${membership.branch.name} - ${membership.branch.business.name}`;
            if (membership.branch.id === activeBranchId) {
                option.selected = true;
            }
            select.appendChild(option);
        });

        // Manejar el cambio de sucursal
        select.addEventListener('change', function () {
            if (this.value) {
                window.location.href = `/admin/set-active-branch/${this.value}/`;
            }
        });
    }

    // Ejecutar cuando el DOM esté listo
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', createBranchSelector);
    } else {
        createBranchSelector();
    }
})();
