import { useState } from "react";

import { WelcomeDialog } from "./components/WelcomeDialog";
import { LeftRail } from "./components/layout/LeftRail";
import { StatusFooter } from "./components/layout/StatusFooter";
import { TopBar } from "./components/layout/TopBar";
import { InformationPanel } from "./components/orders/InformationPanel";
import { OrderRequestForm } from "./components/orders/OrderRequestForm";
import { OrderSelector } from "./components/orders/OrderSelector";
import { Tabs } from "./components/orders/Tabs";
import { TotalsFooter } from "./components/orders/TotalsFooter";
import { useOrderGenerator } from "./hooks/useOrderGenerator";
import { useWelcomeDialog } from "./hooks/useWelcomeDialog";

export default function App() {
  const [prompt, setPrompt] = useState("");
  const generator = useOrderGenerator();
  const welcome = useWelcomeDialog();

  function handleSubmit(event) {
    event.preventDefault();
    const submitted = prompt;
    setPrompt("");
    generator.submit(submitted);
  }

  function applyExample(example) {
    setPrompt(example);
    welcome.dismiss();
  }

  return (
    <main className="flex h-screen min-w-0 flex-col overflow-hidden bg-slate-50 text-slate-900">
      <WelcomeDialog
        onClose={welcome.dismiss}
        onUsePrompt={applyExample}
        open={welcome.isOpen}
      />
      <TopBar onHelp={welcome.reopen} />
      <div className="flex min-h-0 flex-1">
        <LeftRail />
        <section className="flex min-w-0 flex-1 flex-col gap-4 overflow-y-auto p-4 lg:p-6">
          <OrderRequestForm
            error={generator.error}
            isLoading={generator.isLoading}
            lastPrompt={generator.lastPrompt}
            onPromptChange={setPrompt}
            onSubmit={handleSubmit}
            orderCount={generator.orders.length}
            prompt={prompt}
            selectedIndex={generator.selectedOrderIndex}
            selectedOrder={generator.selectedOrder}
          />
          <div className="flex min-h-[320px] flex-1 flex-col overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
            <OrderSelector
              onSelect={generator.selectOrder}
              orders={generator.orders}
              selectedIndex={generator.selectedOrderIndex}
            />
            <Tabs activeTab={generator.activeTab} onChange={generator.selectTab} />
            <InformationPanel
              activeTab={generator.activeTab}
              orders={generator.orders}
              selectedOrder={generator.selectedOrder}
            />
            <TotalsFooter orders={generator.orders} />
          </div>
        </section>
      </div>
      <StatusFooter
        error={generator.error}
        isLoading={generator.isLoading}
        orders={generator.orders}
      />
    </main>
  );
}
