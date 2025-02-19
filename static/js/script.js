document.addEventListener("DOMContentLoaded", function () {
    // Animasi untuk tabel saat hasil muncul
    let searchForm = document.querySelector("form");
    let table = document.querySelector(".table");
  
    if (table) {
      table.style.opacity = 0;
      setTimeout(() => {
        table.style.opacity = 1;
        table.style.transition = "opacity 0.5s ease-in-out";
      }, 500);
    }
  
    // Validasi Form sebelum submit
    searchForm.addEventListener("submit", function (event) {
      let companyName = document.getElementById("search").value.trim();
      let phlDateStart = document.getElementById("start_date").value.trim();
      let phlDateEnd = document.getElementById("end_date").value.trim();
      let paymentStartDate = document.getElementById("payment_start_date").value.trim();
      let paymentEndDate = document.getElementById("payment_end_date").value.trim();
  
      if (!companyName && !phlDateStart && !phlDateEnd && !paymentStartDate && !paymentEndDate) {
        alert("Harap isi setidaknya satu kolom pencarian!");
        event.preventDefault();
      }
    
      document.querySelector("form").addEventListener("submit", function(event) {
        let formData = new FormData(this);
        console.log("Data dikirim:", Object.fromEntries(formData));
      });
    
    
      // Validasi rentang tanggal
      if (phlDateStart && phlDateEnd && new Date(phlDateStart) > new Date(phlDateEnd)) {
        alert('Tanggal LHP Mulai tidak boleh lebih besar dari Tanggal LHP Selesai!');
        event.preventDefault();
      }
  
      if (paymentStartDate && paymentEndDate && new Date(paymentStartDate) > new Date(paymentEndDate)) {
        alert('Tanggal Pembayaran Mulai tidak boleh lebih besar dari Tanggal Pembayaran Selesai!');
        event.preventDefault();
      }
    });
  
    document.getElementById('scrollTop').addEventListener('click', function () {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  
    document.getElementById('scrollBottom').addEventListener('click', function () {
      window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
    });
  
    // Smooth scroll untuk tautan anchor
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
      anchor.addEventListener('click', function (event) {
        event.preventDefault();
        document.querySelector(this.getAttribute('href')).scrollIntoView({
          behavior: 'smooth',
        });
      });
    });
  });
 
  document.addEventListener("DOMContentLoaded", function () {
    let searchForm = document.querySelector("form");
    let loadingSpinner = document.getElementById("loading-spinner");
  
    searchForm.addEventListener("submit", function (event) {
      loadingSpinner.style.visibility = "visible";
    });
  });
document.addEventListener("DOMContentLoaded", function () {
  let searchForm = document.querySelector("form");
  let loadingSpinner = document.getElementById("loading-spinner");

  searchForm.addEventListener("submit", function (event) {
    loadingSpinner.style.visibility = "visible";
  });
});
document.addEventListener("DOMContentLoaded", function () {
  let searchForm = document.querySelector("form");
  let loadingSpinner = document.getElementById("loading-spinner");

  searchForm.addEventListener("submit", function (event) {
    loadingSpinner.style.visibility = "visible";
  });
});
document.addEventListener("DOMContentLoaded", function () {
  let searchForm = document.querySelector("form");
  let loadingSpinner = document.getElementById("loading-spinner");

  searchForm.addEventListener("submit", function (event) {
    loadingSpinner.style.visibility = "visible";
  });
});

document.addEventListener("DOMContentLoaded", function () {
    let searchForm = document.querySelector("form");
    let loadingSpinner = document.getElementById("loading-spinner");
  
    searchForm.addEventListener("submit", function (event) {
      loadingSpinner.style.visibility = "visible";
    });
  });
  // Ensure the DOM content is fully loaded before adding event listeners
  document.addEventListener('DOMContentLoaded', function () {
    document.getElementById('scrollTop').addEventListener('click', function () {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });

    document.getElementById('scrollBottom').addEventListener('click', function () {
      window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
    });
  });
  