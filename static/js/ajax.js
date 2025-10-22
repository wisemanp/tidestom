document.addEventListener("DOMContentLoaded", function() {
  function renderTable(rows) {
  console.log(rows)
  if (!rows.length) return "<p>No data</p>";
 
  let html = "<div class='table-responsive'>"; 
  html += "<table class='table table-hover table-sm table-bordered'>";
  const keys = Object.keys(rows[0]);
  
  // header
  html += "<thead><tr>";
  keys.forEach(k => { html += `<th>${k}</th>`; });
  html += "</tr></thead><tbody>";

  // rows
  rows.forEach(row => {
    html += "<tr>";
    keys.forEach(k => { html += `<td>${row[k]}</td>`; });
    html += "</tr>";
  });
  
  html += "</tbody></table>";
  html += "</div>";
  return html;
}
  document.querySelectorAll(".ajax-form").forEach(form => {
    const resultDiv = document.getElementById(form.dataset.resultId);
    const submitBtn = form.querySelector('button[type="submit"], input[type="submit"]');

    form.addEventListener("submit", async function(e) {
      e.preventDefault();

      const formData = new FormData(form);

      // Include multi-selects
      form.querySelectorAll("select[multiple]").forEach(select => {
        Array.from(select.selectedOptions).forEach(option => {
          formData.append(select.name, option.value);
        });
      });
      
      // Normalise checkboxes: always send true/false
	  form.querySelectorAll('input[type="checkbox"]').forEach(cb => {
  		formData.set(cb.name, cb.checked ? "true" : "false");
	  });


      // Grey out form + show spinner in button
      form.classList.add("form-disabled");
      let originalText = submitBtn.innerHTML;
      submitBtn.disabled = true;
      submitBtn.innerHTML = '<span class="spinner"></span>';

      try {
        const response = await fetch(form.action, {
          method: "POST",
          body: formData
        });

        const json = await response.json();

        if (json.success) {
          console.log(json.data.data)
          resultDiv.innerHTML = renderTable(json.data.data.table);
        } else {
          resultDiv.innerHTML = `<p style="color:red;">Error: ${json.error || JSON.stringify(json.errors)}</p>`;
        }

      } catch (err) {
        resultDiv.innerHTML = `<p style="color:red;">AJAX failed: ${err}</p>`;
        console.error(err);
      } finally {
        // Restore form + button
        form.classList.remove("form-disabled");
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalText;
      }
      return false;
    });
  });
});
