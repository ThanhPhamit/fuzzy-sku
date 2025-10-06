/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                primary: {
                    DEFAULT: '#2E8500',
                    50: '#E8F5E0',
                    100: '#D1EBC1',
                    200: '#A3D783',
                    300: '#75C345',
                    400: '#47AF07',
                    500: '#2E8500',
                    600: '#256A00',
                    700: '#1C5000',
                    800: '#133500',
                    900: '#0A1B00',
                },
            },
            fontFamily: {
                sans: ['Inter', 'Roboto', 'system-ui', 'sans-serif'],
            },
            animation: {
                'fadeIn': 'fadeIn 0.3s ease-in-out',
                'slideDown': 'slideDown 0.2s ease-out',
                'bounce': 'bounce 2s infinite',
            },
            keyframes: {
                fadeIn: {
                    '0%': { opacity: '0', transform: 'translateY(-10px)' },
                    '100%': { opacity: '1', transform: 'translateY(0)' },
                },
                slideDown: {
                    '0%': { opacity: '0', transform: 'translateY(-10px)' },
                    '100%': { opacity: '1', transform: 'translateY(0)' },
                },
            },
        },
    },
    plugins: [],
}
