export default function LiveLogs({ logs }) {
  return (
    <section className="panel logs-panel">
      <h2>Live Logs</h2>
      <div className="logs-box">
        {logs.length === 0 ? (
          <p>Live processing updates will appear here.</p>
        ) : null}
        {logs.map((log, index) => (
          <div className="log-line" key={`${log}-${index}`}>
            {log}
          </div>
        ))}
      </div>
    </section>
  );
}
