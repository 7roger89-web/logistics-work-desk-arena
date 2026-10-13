// LOGI-197 hook-ordering regression — zero-node -> populated transition.
//
// Renders the REAL ShipmentJourney component directly (same mounted instance)
// first with zero Journey nodes, then re-renders with a populated Journey for
// the SAME shipment id. A conditional early return placed before Hooks would
// make React throw "Rendered more hooks than during the previous render".
import React from 'react';
import { createRoot } from 'react-dom/client';
import ShipmentJourney from '../../component/src/components/ShipmentJourney';
import { StoreProvider } from '../../component/src/lib/store';

declare global {
  interface Element {
    __journeyRoot?: ReturnType<typeof createRoot>;
  }
}

export function renderJourney(container: Element, shipment: any) {
  const root = container.__journeyRoot ?? createRoot(container);
  container.__journeyRoot = root;
  root.render(
    <StoreProvider>
      <ShipmentJourney
        shipment={shipment}
        activeStage=""
        work="overview"
        onOpen={() => false}
        onGlobal={() => false}
        runPrimary={() => {}}
      />
    </StoreProvider>
  );
}

export function unmountJourney(container: Element) {
  container.__journeyRoot?.unmount();
  delete container.__journeyRoot;
}
