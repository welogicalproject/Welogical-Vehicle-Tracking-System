export const TRACKING_MAP_STYLES = `
  .vts-vehicle-marker div {
    width: 16px;
    height: 16px;
    border-radius: 999px;
    border: 2px solid #ffffff;
    box-shadow: 0 0 0 4px rgba(15, 23, 42, 0.4), 0 4px 10px rgba(0, 0, 0, 0.5);
    transition: all 0.2s ease-in-out;
  }
  .vts-vehicle-marker:hover div {
    transform: scale(1.2);
    box-shadow: 0 0 0 6px rgba(15, 23, 42, 0.6), 0 6px 14px rgba(0, 0, 0, 0.6);
  }
  .vts-direction-arrow {
    text-shadow: 0 1px 4px rgba(0, 0, 0, 0.8);
    font-weight: bold;
  }
  .vts-map-label {
    background: #0f172a !important;
    border: 1px solid #1e294b !important;
    color: #f1f5f9 !important;
    border-radius: 6px !important;
    padding: 2px 6px !important;
    font-size: 10px !important;
    font-weight: 700 !important;
    font-family: ui-sans-serif, system-ui, sans-serif !important;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3) !important;
  }
  .vts-map-label::before {
    border-right-color: #1e294b !important;
  }
  .vts-popup {
    min-width: 200px;
    font-family: ui-sans-serif, system-ui, sans-serif;
    font-size: 11px;
    padding: 2px;
  }
  .vts-popup strong {
    display: block;
    color: #22d3ee;
    font-size: 13px;
    font-weight: 800;
  }
  .vts-popup code {
    display: block;
    color: #94a3b8;
    font-size: 10px;
    margin: 1px 0 6px;
  }
  .vts-popup dl {
    display: grid;
    grid-template-columns: 74px 1fr;
    gap: 3px 6px;
    margin: 0;
    border-top: 1px solid #1e294b/50;
    padding-top: 6px;
  }
  .vts-popup dt {
    color: #64748b;
    font-weight: 600;
  }
  .vts-popup dd {
    margin: 0;
    color: #cbd5e1;
    font-weight: 500;
  }
  .vts-popup a {
    display: block;
    margin-top: 8px;
    border: 1px solid #06b6d4/60;
    background: #06b6d4/10;
    border-radius: 6px;
    padding: 4px 6px;
    color: #22d3ee;
    text-align: center;
    font-weight: 700;
    text-decoration: none;
    transition: all 0.2s;
  }
  .vts-popup a:hover {
    background: #06b6d4/25;
    color: #fff;
  }
`;
