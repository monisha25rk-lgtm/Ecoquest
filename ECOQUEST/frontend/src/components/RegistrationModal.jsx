import { CheckCircle2, X } from "lucide-react";

export default function RegistrationModal({ open, event, loading, error, success, onClose, onConfirm }) {
  if (!open) return null;
  return (
    <div className="modal-backdrop" role="presentation" onMouseDown={(eventClick) => eventClick.target === eventClick.currentTarget && onClose()}>
      <section className="modal-card" role="dialog" aria-modal="true" aria-labelledby="registration-title">
        <button className="icon-button modal-close" type="button" onClick={onClose} aria-label="Close"><X size={19} /></button>
        {success ? (
          <><span className="modal-success-icon"><CheckCircle2 size={26} /></span><h2 id="registration-title">You’re on the list!</h2><p>Your registration for <strong>{event.title}</strong> is confirmed. You can find it in My Activities.</p><button className="button-primary full-button" onClick={onClose}>Done</button></>
        ) : (
          <><span className="eyebrow">READY TO MAKE AN IMPACT?</span><h2 id="registration-title">Join this event</h2><p>Confirm your registration for <strong>{event.title}</strong>.</p>{error && <div className="form-error" role="alert">{error}</div>}<div className="modal-actions"><button className="button-secondary" type="button" onClick={onClose}>Not now</button><button className="button-primary" type="button" disabled={loading} onClick={onConfirm}>{loading ? "Registering…" : "Confirm registration"}</button></div></>
        )}
      </section>
    </div>
  );
}
