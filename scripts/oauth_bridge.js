import http from 'http'

const server = http.createServer((req, res) => {
  res.writeHead(200, {
    'Content-Type': 'text/html; charset=utf-8',
    'Cache-Control': 'no-store, no-cache, must-revalidate',
  })
  res.end(`<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Authenticating with Sahachari...</title>
</head>
<body style="font-family: sans-serif; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; background: #fffdf9; color: #7a3e2d;">
  <div style="text-align: center;">
    <h2>Completing sign-in...</h2>
    <p>Redirecting you to Shree Financial Companion on port 5173...</p>
  </div>
  <script>
    var target = "http://localhost:5173" + window.location.pathname + window.location.search + window.location.hash;
    window.location.replace(target);
  </script>
</body>
</html>`)
})

server.listen(3000, '0.0.0.0', () => {
  console.log('OAuth Bridge running on http://localhost:3000 -> forwarding to http://localhost:5173')
})
