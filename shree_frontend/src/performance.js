export function reportFrontendLoad() {
  if (typeof window === 'undefined' || typeof performance === 'undefined') return

  const report = () => {
    const navigation = performance.getEntriesByType('navigation')[0]
    const loadMs = navigation?.loadEventEnd || performance.now()
    console.info('[sahachari.performance]', {
      metric: 'frontend.load',
      load_ms: Math.round(loadMs * 100) / 100,
      transfer_size: navigation?.transferSize ?? null,
    })
  }

  if (document.readyState === 'complete') {
    window.setTimeout(report, 0)
  } else {
    window.addEventListener('load', report, { once: true })
  }
}
