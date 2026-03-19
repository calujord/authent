// Script para inyectar el avatar del usuario en el header de Unfold
(function () {
    'use strict';

    function injectUserAvatar() {
        // Buscar el contenedor del usuario en el header
        const userMenuTrigger = document.querySelector('[data-toggle="dropdown"]');
        const userLinks = document.querySelectorAll('a[href="/admin/logout/"], a[href*="password"]');

        if (!userMenuTrigger && userLinks.length === 0) {
            return;
        }

        // Obtener datos del usuario desde el DOM
        const userInfoElement = document.querySelector('.user-menu-container');

        if (!userInfoElement) {
            return;
        }

        // Buscar el avatar existente en user_menu
        const avatarImg = userInfoElement.querySelector('.user-avatar');
        const avatarPlaceholder = userInfoElement.querySelector('.user-avatar-placeholder');

        // Buscar el botón de menú del usuario en el header (puede variar según la versión de Unfold)
        const headerUserButton = document.querySelector('button[aria-label="User menu"], .unfold-header-user-button, [class*="user-menu-button"]');

        if (headerUserButton) {
            // Limpiar contenido previo
            const existingAvatar = headerUserButton.querySelector('.header-user-avatar');
            if (existingAvatar) {
                return; // Ya existe, no hacer nada
            }

            // Crear elemento de avatar para el header
            let headerAvatar;

            if (avatarImg && avatarImg.src) {
                // Clonar la imagen del avatar
                headerAvatar = document.createElement('img');
                headerAvatar.src = avatarImg.src;
                headerAvatar.alt = avatarImg.alt || 'User avatar';
                headerAvatar.className = 'header-user-avatar user-avatar';
                headerAvatar.style.cssText = 'width: 40px; height: 40px; border-radius: 50%; object-fit: cover; border: 2px solid #14b8a6; margin-right: 8px;';

                headerAvatar.onerror = function () {
                    this.style.display = 'none';
                    if (avatarPlaceholder) {
                        const placeholder = avatarPlaceholder.cloneNode(true);
                        placeholder.className = 'header-user-avatar user-avatar-placeholder';
                        placeholder.style.cssText = 'width: 40px; height: 40px; border-radius: 50%; background: linear-gradient(135deg, #2dd4bf 0%, #14b8a6 50%, #0d9488 100%); display: flex; align-items: center; justify-content: center; color: white; font-weight: 600; font-size: 16px; margin-right: 8px;';
                        this.parentNode.insertBefore(placeholder, this.nextSibling);
                    }
                };
            } else if (avatarPlaceholder) {
                // Clonar el placeholder
                headerAvatar = avatarPlaceholder.cloneNode(true);
                headerAvatar.className = 'header-user-avatar user-avatar-placeholder';
                headerAvatar.style.cssText = 'width: 40px; height: 40px; border-radius: 50%; background: linear-gradient(135deg, #2dd4bf 0%, #14b8a6 50%, #0d9488 100%); display: flex; align-items: center; justify-content: center; color: white; font-weight: 600; font-size: 16px; margin-right: 8px;';
            }

            if (headerAvatar) {
                // Insertar el avatar al inicio del botón
                headerUserButton.insertBefore(headerAvatar, headerUserButton.firstChild);
            }
        }
    }

    // Ejecutar cuando el DOM esté listo
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', injectUserAvatar);
    } else {
        injectUserAvatar();
    }

    // También ejecutar después de un pequeño delay por si Unfold carga dinámicamente
    setTimeout(injectUserAvatar, 500);
    setTimeout(injectUserAvatar, 1000);
})();
