/* app.js – Talent Connect CRM portal JS */

/**
 * Toggle an inline edit row in entity tables.
 * @param {string} key  e.g. "emp-12" or "client-7"
 */
function toggleEdit(key) {
  const editRow = document.getElementById('edit-' + key);
  if (!editRow) return;
  editRow.classList.toggle('hidden');
}
