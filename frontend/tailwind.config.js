export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      keyframes: {
        indeterminate: {
          '0%':   { transform: 'translateX(-100%) scaleX(0.4)' },
          '50%':  { transform: 'translateX(50%)  scaleX(0.6)' },
          '100%': { transform: 'translateX(300%) scaleX(0.4)' },
        },
      },
      animation: {
        indeterminate: 'indeterminate 1.4s ease-in-out infinite',
      },
    },
  },
  plugins: [],
}
