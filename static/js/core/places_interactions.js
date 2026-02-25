/**
 * IBB GUIDE - PLACES INTERACTIONS
 * Handles specific interactions for place pages (Favorites, etc.)
 * Depends on: Http (core/http.js)
 */

const PlacesInteractions = {
    /**
     * Init all listeners
     */
    init() {
        this.bindFavoriteButtons();
    },

    /**
     * Bind click events to any .favorite-btn
     */
    bindFavoriteButtons() {
        document.querySelectorAll('.favorite-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const placeId = btn.getAttribute('data-place-id');
                if (placeId) {
                    this.toggleFavorite(placeId, btn);
                }
            });
        });
    },

    /**
     * Toggle Favorite Status
     */
    async toggleFavorite(placeId, btnElement) {
        // Optimistic UI Update (optional, or wait for server)
        // Here we wait for server to be safe

        const url = `/place/${placeId}/favorite/`;

        try {
            const result = await Http.post(url, {});

            if (result.status === 401) {
                // Http helper already handles redirect, but we can double check or show modal
                // If Http.js handles it, we stop here.
                return;
            }

            if (result.ok && result.data) {
                this.updateFavoriteUI(btnElement, result.data.liked);
            } else {
                console.error('Favorite toggle failed:', result.error);
                // Optional: Toast error
            }

        } catch (error) {
            console.error('Network error during favorite toggle:', error);
        }
    },

    /**
     * Update the button UI based on state
     */
    updateFavoriteUI(btn, isLiked) {
        const icon = btn.querySelector('i');
        const textSpan = btn.querySelector('.fav-text'); // If we have text span

        if (isLiked) {
            if (icon) {
                icon.classList.remove('far');
                icon.classList.add('fas');
            }
            btn.classList.add('active'); // Optional styling hook
        } else {
            if (icon) {
                icon.classList.remove('fas');
                icon.classList.add('far');
            }
            btn.classList.remove('active');
        }
    }
};

// Auto-init on DOM Ready
document.addEventListener('DOMContentLoaded', () => {
    PlacesInteractions.init();
});
