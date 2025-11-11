document.addEventListener("DOMContentLoaded", function() {

  function renderTable(rows) {
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

    html += "</tbody></table></div>";
    return html;
  }

  document.querySelectorAll(".ajax-form").forEach(form => {
    const resultDiv = document.getElementById(form.dataset.resultId);
    const submitBtn = form.querySelector('button[type="submit"], input[type="submit"]');

    form.addEventListener("submit", async function(e) {
      e.preventDefault();
      if (form.dataset.submitting) return false; // prevent double submission
      form.dataset.submitting = "true";

      const formData = new FormData(form);

      // Multi-selects
      form.querySelectorAll("select[multiple]").forEach(select => {
        Array.from(select.selectedOptions).forEach(option => {
          formData.append(select.name, option.value);
        });
      });

      // Checkboxes
      form.querySelectorAll('input[type="checkbox"]').forEach(cb => {
        formData.set(cb.name, cb.checked ? "true" : "false");
      });

      // Disable form + spinner
      form.classList.add("form-disabled");
      let originalText = submitBtn.innerHTML;
      submitBtn.disabled = true;
      submitBtn.innerHTML = '<span class="spinner"></span>';

      try {
        const response = await fetch(form.action, { method: "POST", body: formData });
        const json = await response.json();

        if (json.success) {
          // Render table
          if (json.data?.data?.table) {
            resultDiv.innerHTML = renderTable(json.data.data.table);
          }

          // SNID-specific HTMX
          if (form.id === "snid-form") {
          	console.log('Sending SNID fits...');
            const filePath = json.data.data.file_path;
            const container = document.getElementById('spectroscopy');
            const targetId = container.dataset.targetId;

            htmx.ajax('GET',
              `/marshal/target_spectroscopy/${targetId}/?snid_path=${encodeURIComponent(filePath)}`,
              { target: '#spectroscopy' }
            );
          }

          // NGSF-specific HTMX
          if (form.id === "ngsf-form") {
            const filePath = json.data.data.file_path;
            const container = document.getElementById('spectroscopy');
            const targetId = container.dataset.targetId;

            htmx.ajax('GET',
              `/target_spectroscopy/${targetId}/?ngsf_path=${encodeURIComponent(filePath)}`,
              { target: '#spectroscopy' }
            );
          }

        } else {
          resultDiv.innerHTML = `<p style="color:red;">Error: ${json.error || JSON.stringify(json.errors)}</p>`;
        }

      } catch (err) {
        resultDiv.innerHTML = `<p style="color:red;">AJAX failed: ${err}</p>`;
        console.error(err);
      } finally {
        form.dataset.submitting = "false";
        form.classList.remove("form-disabled");
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalText;
      }

      return false;
    });
  });

});
