import { useEffect, useRef, useState } from "react";

const API = "http://127.0.0.1:8000";
const R = 110;
const CIRC = 2 * Math.PI * R;

export default function App() {
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const [notify, setNotify] = useState(
    typeof Notification !== "undefined" ? Notification.permission : "denied"
  );
  const warned = useRef(null);

  const load = async () => {
    try {
      const r = await fetch(`${API}/today`);
      if (!r.ok) throw new Error(`API returned ${r.status}`);
      setData(await r.json());
      setErr(null);
    } catch {
      setErr("Can't reach the API. Start it with: uvicorn main:app --reload");
    }
  };

  const send = async (path, method) => {
    try {
      const r = await fetch(`${API}${path}`, {
        method,
        headers: { "Content-Type": "application/json" },
        body: method === "POST" ? JSON.stringify({ ml: 250 }) : undefined,
      });
      if (r.ok) setData(await r.json());
    } catch {
      setErr("That didn't save. Check the API is still running.");
    }
  };

  useEffect(() => {
    load();
    const id = setInterval(load, 60_000);
    return () => clearInterval(id);
  }, []);

  // Fire a reminder when you fall behind pace — once per scheduled slot.
  useEffect(() => {
    if (!data?.next || notify !== "granted") return;
    if (data.behind_by_ml > 0 && warned.current !== data.sips_logged) {
      warned.current = data.sips_logged;
      new Notification("Time to drink", {
        body: `${data.behind_by_ml} ml behind pace. Next sip: ${data.next.ml} ml.`,
        tag: "drip-sip",
      });
    }
  }, [data, notify]);

  if (err && !data) return <Shell><p className="err">{err}</p></Shell>;
  if (!data) return <Shell><p className="muted">Loading your day…</p></Shell>;

  const litres = (data.drunk_ml / 1000).toFixed(1);
  const goalL = (data.goal_ml / 1000).toFixed(1);

  return (
    <Shell>
      <header className="brand">
        <div>
          <h1>DR<b>I</b>P</h1>
          <p className="tag">your day, in sips</p>
        </div>
        {data.streak > 0 && (
          <div className="streak">
            <span>{data.streak}</span>
            <small>DAY<br />STREAK</small>
          </div>
        )}
      </header>

      <div className="core">
        <svg viewBox="0 0 260 260" className="ring">
          <defs>
            <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0" stopColor="#35E0D0" />
              <stop offset="1" stopColor="#6FC2FF" />
            </linearGradient>
          </defs>
          <circle cx="130" cy="130" r={R} className="track" />
          <circle
            cx="130" cy="130" r={R} className="fill"
            strokeDasharray={CIRC}
            strokeDashoffset={CIRC * (1 - Math.min(1, data.pct / 100))}
          />
        </svg>
        <div className="readout">
          <div className="big">{litres}<i>L</i></div>
          <div className="muted">of {goalL} L goal</div>
          <div className="pct">{data.pct}% HYDRATED</div>
        </div>
      </div>

      <div className="sips">
        {Array.from({ length: data.sips_planned }, (_, i) => (
          <div
            key={i}
            className={
              "sip" +
              (i < data.sips_logged ? " done" : "") +
              (i === data.sips_logged ? " now" : "")
            }
          >
            <i />
          </div>
        ))}
      </div>

      {data.next && (
        <div className="next">
          <div>
            <div className="lab">Next sip</div>
            <div className="when">{data.next.at}</div>
          </div>
          <div className="ml">
            <b>{data.next.ml}</b><small>ML</small>
          </div>
        </div>
      )}

      {data.behind_by_ml > 0 && (
        <p className="behind">{data.behind_by_ml} ml behind pace</p>
      )}

      <div className="actions">
        <button className="primary" onClick={() => send("/log", "POST")}>
          Log 250 ml
        </button>
        <button onClick={() => send("/log/last", "DELETE")} disabled={!data.sips_logged}>
          Undo
        </button>
      </div>

      {notify !== "granted" && (
        <button
          className="link"
          onClick={() => Notification.requestPermission().then(setNotify)}
        >
          Turn on reminders
        </button>
      )}

      {err && <p className="err">{err}</p>}
    </Shell>
  );
}

function Shell({ children }) {
  return (
    <>
      <style>{CSS}</style>
      <div className="stage"><div className="caustic" /><main>{children}</main></div>
    </>
  );
}

const CSS = `
@import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,600;12..96,800&family=JetBrains+Mono:wght@400;500;700&family=Instrument+Sans:wght@400;500;600&display=swap');
:root{--chlorine:#35E0D0;--sodium:#FFB847;--foam:#EAF7F5;--slate:#7FB3C4;
  --display:'Bricolage Grotesque',system-ui,sans-serif;--mono:'JetBrains Mono',monospace;--body:'Instrument Sans',system-ui,sans-serif}
*{box-sizing:border-box;margin:0}
body{background:#061A26}
.stage{min-height:100vh;position:relative;overflow:hidden;
  background:linear-gradient(180deg,#0E3A4F,#082431 60%,#061A26)}
.caustic{position:absolute;inset:-25%;opacity:.28;mix-blend-mode:screen;pointer-events:none;filter:blur(14px);
  background:radial-gradient(38% 22% at 20% 30%,rgba(53,224,208,.5),transparent 60%),
             radial-gradient(30% 18% at 72% 22%,rgba(53,224,208,.36),transparent 60%);
  animation:caust 14s ease-in-out infinite alternate}
@keyframes caust{to{transform:translate3d(4%,-3%,0) scale(1.14)}}
main{position:relative;max-width:460px;margin:0 auto;padding:36px 26px 48px;
  display:flex;flex-direction:column;align-items:center;gap:22px;font-family:var(--body)}
.brand{width:100%;display:flex;align-items:center;justify-content:space-between}
.brand h1{font:800 40px/1 var(--display);color:var(--foam);letter-spacing:-.045em}
.brand h1 b{color:var(--chlorine)}
.tag{font:500 11px/1 var(--mono);color:var(--slate);letter-spacing:.2em;text-transform:uppercase;margin-top:7px}
.streak{display:flex;align-items:center;gap:8px;padding:9px 15px;border-radius:999px;
  background:rgba(255,184,71,.11);border:1px solid rgba(255,184,71,.34)}
.streak span{font:700 20px/1 var(--mono);color:var(--sodium)}
.streak small{font:500 9px/1.25 var(--mono);color:#C79A56;letter-spacing:.1em}
.core{position:relative;width:260px;height:260px;display:grid;place-items:center}
.ring{position:absolute;inset:0;transform:rotate(-90deg)}
.track{stroke:rgba(234,247,245,.1);stroke-width:9;fill:none}
.fill{stroke:url(#g);stroke-width:9;fill:none;stroke-linecap:round;
  transition:stroke-dashoffset .9s cubic-bezier(.33,1,.68,1);filter:drop-shadow(0 0 10px rgba(53,224,208,.6))}
.readout{text-align:center;z-index:1}
.big{font:700 66px/.9 var(--display);color:var(--foam);letter-spacing:-.05em;font-variant-numeric:tabular-nums}
.big i{font-size:26px;font-style:normal;color:var(--chlorine)}
.muted{font:500 13px/1 var(--mono);color:var(--slate);margin-top:6px}
.pct{margin-top:10px;font:700 11px/1 var(--mono);color:var(--chlorine);letter-spacing:.16em}
.sips{display:flex;gap:8px;flex-wrap:wrap;justify-content:center}
.sip{width:32px;height:46px;border-radius:5px 5px 9px 9px;border:2px solid rgba(234,247,245,.2);
  position:relative;overflow:hidden;background:rgba(234,247,245,.045)}
.sip i{position:absolute;inset:auto 0 0 0;height:0;transition:height .5s cubic-bezier(.33,1,.68,1);
  background:linear-gradient(180deg,var(--chlorine),#1B8FA0)}
.sip.done i{height:100%}
.sip.now{border-color:var(--sodium);box-shadow:0 0 0 3px rgba(255,184,71,.16)}
.next{width:100%;display:flex;align-items:center;gap:14px;padding:16px 20px;border-radius:16px;
  background:rgba(7,26,43,.6);border:1px solid rgba(53,224,208,.2);backdrop-filter:blur(8px)}
.lab{font:500 10px/1 var(--mono);color:var(--slate);letter-spacing:.16em;text-transform:uppercase}
.when{font:700 24px/1 var(--display);color:var(--foam);letter-spacing:-.03em;margin-top:7px}
.ml{margin-left:auto;text-align:right}
.ml b{display:block;font:700 26px/1 var(--display);color:var(--chlorine);letter-spacing:-.03em}
.ml small{font:500 9px/1 var(--mono);color:var(--slate);letter-spacing:.1em}
.behind{font:500 13px/1 var(--mono);color:var(--sodium)}
.actions{display:flex;gap:10px;width:100%}
button{flex:1;padding:15px;border-radius:12px;cursor:pointer;font:600 15px/1 var(--body);
  border:1px solid rgba(53,224,208,.3);background:transparent;color:var(--foam);transition:.15s}
button:hover:not(:disabled){border-color:var(--chlorine)}
button:disabled{opacity:.35;cursor:not-allowed}
button:focus-visible{outline:2px solid var(--chlorine);outline-offset:2px}
.primary{background:var(--chlorine);color:#062028;border-color:var(--chlorine);flex:2}
.link{flex:0;border:none;background:none;color:var(--slate);font-size:13px;text-decoration:underline;padding:4px}
.err{font:500 13px/1.5 var(--mono);color:#FF8FB0;text-align:center}
@media (prefers-reduced-motion:reduce){.caustic{animation:none}.fill,.sip i{transition:none}}
`;
