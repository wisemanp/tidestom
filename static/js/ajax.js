document.addEventListener("DOMContentLoaded", function() {
  document.querySelectorAll(".ajax-form").forEach(form => {
    const resultDiv = document.getElementById(form.dataset.resultId);

    form.addEventListener("submit", async function(e) {
      e.preventDefault();

      const formData = new FormData(form);

      // Include multi-selects
      form.querySelectorAll("select[multiple]").forEach(select => {
        Array.from(select.selectedOptions).forEach(option => {
          formData.append(select.name, option.value);
        });
      });

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
      }
    });
  });
});
