export default function PrototypeDeviceFrame({ children, compact = false }) {
  return (
    <div
      className={`prototype-device mx-auto ${compact ? 'prototype-device--compact' : ''}`}
      aria-label="Prototype round device preview"
    >
      <div className="prototype-device__side prototype-device__side--left" aria-hidden="true" />
      <div className="prototype-device__face">
        <div className="prototype-device__screen">
          {children}
        </div>
        <div className="prototype-device__controls" aria-hidden="true">
          <span />
          <span />
          <span />
        </div>
      </div>
      <div className="prototype-device__button" aria-hidden="true" />
    </div>
  );
}
