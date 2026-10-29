from pathlib import Path

file_path = Path("frontend01/src/pages/InventoryPage.tsx")
content = file_path.read_text(encoding="utf-8")

# Add import of InfoTooltip and ConfirmModal
import_target = "import { useCanteen } from '../context/CanteenContext';"
import_replacement = """import { useCanteen } from '../context/CanteenContext';
import { InfoTooltip } from '../components/InfoTooltip';
import { ConfirmModal } from '../components/ConfirmModal';"""

if import_target in content:
    content = content.replace(import_target, import_replacement)

# Add confirm modal state
state_target = "  const [adjustmentType, setAdjustmentType] = useState<'restock' | 'usage'>('usage');"
state_replacement = """  const [adjustmentType, setAdjustmentType] = useState<'restock' | 'usage'>('usage');
  const [poConfirmModal, setPoConfirmModal] = useState<{ isOpen: boolean; title: string; message: string; action: () => void }>({
    isOpen: false,
    title: '',
    message: '',
    action: () => {},
  });"""

if state_target in content:
    content = content.replace(state_target, state_replacement)

# Update handlePlaceOrder to use confirm modal
po_target = """  const handlePlaceOrder = (rec: any) => {
    api.placeOrder({
      ingredient_id: rec.ingredient_id,
      quantity: rec.suggested_order,
      supplier: rec.supplier,
      unit_cost: rec.avg_cost,
    })
      .then(() => {
        addToast(`Purchase Order created: ${rec.suggested_order} ${rec.unit} of ${rec.ingredient_name} ordered from ${rec.supplier}`, 'success');
        loadData();
      })
      .catch((err) => {
        addToast(`Failed to place order: ${err.message}`, 'error');
      });
  };"""

po_replacement = """  const handlePlaceOrder = (rec: any) => {
    setPoConfirmModal({
      isOpen: true,
      title: `Create Purchase Order: ${rec.ingredient_name}`,
      message: `Are you sure you want to place a purchase order for ${rec.suggested_order} ${rec.unit} of ${rec.ingredient_name} with ${rec.supplier} for an estimated cost of ₹${rec.estimated_procurement_cost.toLocaleString()}?`,
      action: () => {
        api.placeOrder({
          ingredient_id: rec.ingredient_id,
          quantity: rec.suggested_order,
          supplier: rec.supplier,
          unit_cost: rec.avg_cost,
        })
          .then(() => {
            addToast(`Purchase Order created: ${rec.suggested_order} ${rec.unit} of ${rec.ingredient_name} ordered from ${rec.supplier}`, 'success');
            loadData();
          })
          .catch((err) => {
            addToast(`Failed to place order: ${err.message}`, 'error');
          });
        setPoConfirmModal((prev) => ({ ...prev, isOpen: false }));
      },
    });
  };"""

if po_target in content:
    content = content.replace(po_target, po_replacement)

# Update procurement table to dense with sticky headers & responsive styling
proc_table_target = """          <div className="table-container">
            <table className="enterprise-table">
              <thead>
                <tr>
                  <th>Urgency</th>
                  <th>Ingredient</th>
                  <th>Current Stock</th>
                  <th>Menu Requirement</th>
                  <th>Suggested Order</th>
                  <th>Est. Cost</th>
                  <th>Supplier & Lead Time</th>
                  <th>Explanation & Rationale</th>
                  <th>Action</th>
                </tr>
              </thead>"""

proc_table_replacement = """          <div className="table-container" style={{ maxHeight: '380px' }}>
            <table className="enterprise-table dense-table" style={{ minWidth: '920px' }}>
              <thead>
                <tr>
                  <th style={{ width: '80px' }}>Urgency</th>
                  <th style={{ width: '160px' }}>Ingredient</th>
                  <th style={{ width: '110px' }}>Current Stock</th>
                  <th style={{ width: '120px' }}>Menu Need</th>
                  <th style={{ width: '110px' }}>Suggested PO</th>
                  <th style={{ width: '90px' }}>Est. Cost</th>
                  <th style={{ width: '150px' }}>Supplier & Lead Time</th>
                  <th>Explanation & Rationale</th>
                  <th style={{ width: '90px' }}>Action</th>
                </tr>
              </thead>"""

if proc_table_target in content:
    content = content.replace(proc_table_target, proc_table_replacement)

# Update Master Inventory table to dense with sticky headers & responsive styling
inv_table_target = """        <div className="table-container">
          <table className="enterprise-table">
            <thead>
              <tr>
                <th>Ingredient Name</th>
                <th>Category</th>
                <th>Current Stock</th>
                <th>Unit</th>
                <th>Avg Cost / Unit</th>
                <th>Reorder Threshold</th>
                <th>Supplier</th>
                <th>Expiry / Batch</th>
                <th>Status</th>
                <th>Quick Actions</th>
              </tr>
            </thead>"""

inv_table_replacement = """        <div className="table-container" style={{ maxHeight: '440px' }}>
          <table className="enterprise-table dense-table" style={{ minWidth: '880px' }}>
            <thead>
              <tr>
                <th style={{ width: '180px' }}>Ingredient Name</th>
                <th style={{ width: '90px' }}>Category</th>
                <th style={{ width: '100px' }}>Stock</th>
                <th style={{ width: '60px' }}>Unit</th>
                <th style={{ width: '90px' }}>Avg Cost</th>
                <th style={{ width: '110px' }}>Threshold</th>
                <th style={{ width: '150px' }}>Supplier</th>
                <th style={{ width: '100px' }}>Expiry</th>
                <th style={{ width: '80px' }}>Status</th>
                <th style={{ width: '110px' }}>Quick Actions</th>
              </tr>
            </thead>"""

if inv_table_target in content:
    content = content.replace(inv_table_target, inv_table_replacement)

# Add ConfirmModal before closing tag
modal_insertion = """      {/* PO Confirmation Modal */}
      <ConfirmModal
        isOpen={poConfirmModal.isOpen}
        title={poConfirmModal.title}
        message={poConfirmModal.message}
        variant="primary"
        confirmLabel="Place PO"
        onConfirm={poConfirmModal.action}
        onCancel={() => setPoConfirmModal((prev) => ({ ...prev, isOpen: false }))}
      />
    </div>
  );
};"""

if "</div>\n  );\n};" in content:
    content = content.replace("</div>\n  );\n};", modal_insertion)
elif "</div>\r\n  );\r\n};" in content:
    content = content.replace("</div>\r\n  );\r\n};", modal_insertion)

file_path.write_text(content, encoding="utf-8")
print("InventoryPage.tsx patched successfully!")
