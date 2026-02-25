/**
 * IBB GUIDE - FEATURES HELPER
 * Manage feature toggles from backend configuration.
 */

const Features = {
    /**
     * Check if a feature is enabled
     * @param {string} key - Feature key (e.g., 'enable_comments')
     * @returns {boolean}
     */
    isEnabled(key) {
        if (!window.APP || !window.APP.features) {
            console.warn('Features not loaded or APP config missing.');
            return false;
        }
        return !!window.APP.features[key];
    },

    /**
     * Execute callback if feature is enabled
     * @param {string} key 
     * @param {Function} callback 
     */
    runIf(key, callback) {
        if (this.isEnabled(key) && typeof callback === 'function') {
            callback();
        }
    }
};

window.Features = Features;
