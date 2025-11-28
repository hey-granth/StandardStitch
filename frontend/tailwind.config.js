/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                background: "var(--bg-app)",
                surface: "var(--bg-surface)",
                "surface-hover": "var(--bg-surface-hover)",
                border: "var(--border-subtle)",
                "border-focus": "var(--border-focus)",
                primary: "var(--primary)",
                "primary-foreground": "var(--primary-foreground)",
                secondary: "var(--text-secondary)",
                muted: "var(--text-muted)",
                accent: "var(--accent)",
                success: "var(--success)",
                error: "var(--error)",
                warning: "var(--warning)",
            },
            fontFamily: {
                sans: ['Inter', 'sans-serif'],
            },
            animation: {
                "fade-in": "fadeIn 0.5s ease-out",
                "slide-up": "slideUp 0.5s ease-out",
            },
            keyframes: {
                fadeIn: {
                    "0%": { opacity: "0" },
                    "100%": { opacity: "1" },
                },
                slideUp: {
                    "0%": { transform: "translateY(20px)", opacity: "0" },
                    "100%": { transform: "translateY(0)", opacity: "1" },
                },
            },
        },
    },
    plugins: [],
}
