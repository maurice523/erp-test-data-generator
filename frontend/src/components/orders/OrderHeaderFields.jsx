import { formatValue } from "../../lib/format";
import { Field } from "../ui/Field";

export function OrderHeaderFields({ selectedOrder }) {
  const address = selectedOrder?.shipToAddress ?? {};
  const contact = selectedOrder?.contact ?? {};

  return (
    <section className="min-w-0 rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <h2 className="mb-3 text-sm font-semibold text-slate-900">Order details</h2>
      <div className="grid grid-cols-2 gap-x-3 gap-y-2.5 md:grid-cols-4">
        <Field
          label="Order number"
          name="orderNo"
          readOnly
          value={formatValue(selectedOrder?.orderNo)}
        />
        <Field
          label="External reference"
          name="externalRefNo"
          readOnly
          value={formatValue(selectedOrder?.externalRefNo)}
        />
        <Field
          label="Customer number"
          name="customerNo"
          readOnly
          value={formatValue(selectedOrder?.customerNo)}
        />
        <Field
          label="PO number"
          name="poNumber"
          readOnly
          value={formatValue(selectedOrder?.poNumber)}
        />
        <Field
          label="Customer contact"
          name="customerContact"
          readOnly
          value={formatValue(contact.emailAddress)}
          wide
        />
        <Field
          label="Shipping method"
          name="shipViaCode"
          readOnly
          value={formatValue(selectedOrder?.shipViaCode)}
        />
        <Field
          label="Status"
          name="status"
          readOnly
          value={selectedOrder ? "Generated" : ""}
        />
        <Field
          label="Ship-to name"
          name="address1"
          readOnly
          value={formatValue(address.address1 || address.address4)}
          wide
        />
        <Field
          label="Ship-to address"
          name="address2"
          readOnly
          value={formatValue(address.address2)}
          wide
        />
        <Field label="City" name="city" readOnly value={formatValue(address.city)} />
        <Field
          label="State / province"
          name="state"
          readOnly
          value={formatValue(address.state)}
        />
        <Field
          label="Postal code"
          name="zipCode"
          readOnly
          value={formatValue(address.zipCode)}
        />
        <Field
          label="Country"
          name="countryCode"
          readOnly
          value={formatValue(address.countryCode)}
        />
      </div>
    </section>
  );
}
