document.addEventListener("DOMContentLoaded", function() {
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
          resultDiv.innerHTML = `<pre>${JSON.stringify(json.data, null, 2)}</pre>`;
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
    });
  });
});
