/**
 * IBB GUIDE - HTTP HELPER
 * Standardized fetch wrapper for consistent API handling.
 */

const Http = {
    async request(url, options = {}) {
        const defaults = {
            headers: {
                'X-CSRFToken': window.APP ? window.APP.csrf : '',
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
        };

        // If body is FormData, remove Content-Type to let browser set it
        if (options.body instanceof FormData) {
            delete defaults.headers['Content-Type'];
        }

        const config = {
            ...defaults,
            ...options,
            headers: {
                ...defaults.headers,
                ...options.headers
            }
        };

        try {
            const response = await fetch(url, config);

            // Handle 401 Unauthorized
            if (response.status === 401) {
                console.warn('Unauthorized request. Redirecting to login...');
                window.location.href = '/accounts/login/?next=' + window.location.pathname;
                return { ok: false, status: 401, error: 'Unauthorized' };
            }

            const data = await response.json().catch(() => ({}));

            if (!response.ok) {
                return {
                    ok: false,
                    status: response.status,
                    error: data.message || data.detail || 'Something went wrong',
                    data
                };
            }

            return { ok: true, status: response.status, data };

        } catch (error) {
            console.error('Network Error:', error);
            return { ok: false, status: 0, error: 'Network Error' };
        }
    },

    get(url) {
        return this.request(url, { method: 'GET' });
    },

    post(url, body) {
        return this.request(url, {
            method: 'POST',
            body: body instanceof FormData ? body : JSON.stringify(body)
        });
    },

    put(url, body) {
        return this.request(url, {
            method: 'PUT',
            body: body instanceof FormData ? body : JSON.stringify(body)
        });
    },

    delete(url) {
        return this.request(url, { method: 'DELETE' });
    }
};

window.Http = Http;
