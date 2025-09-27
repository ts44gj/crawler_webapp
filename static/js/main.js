// メインのJavaScriptファイル

document.addEventListener("DOMContentLoaded", function () {
  // フォーム送信時のローディング表示
  const form = document.querySelector("form");
  if (form) {
    form.addEventListener("submit", function () {
      const submitBtn = form.querySelector('button[type="submit"]');
      if (submitBtn) {
        submitBtn.innerHTML = '<span class="loading"></span> クロール中...';
        submitBtn.disabled = true;
        submitBtn.classList.add("opacity-75", "cursor-not-allowed");
      }
    });
  }

  // URL入力の自動補完
  const urlInput = document.getElementById("url");
  if (urlInput) {
    urlInput.addEventListener("blur", function () {
      let url = this.value.trim();
      if (url && !url.startsWith("http://") && !url.startsWith("https://")) {
        this.value = "http://" + url;
      }
    });
  }

  // アラートの自動非表示
  const alerts = document.querySelectorAll(".alert");
  alerts.forEach(function (alert) {
    setTimeout(function () {
      alert.style.opacity = "0";
      alert.style.transform = "translateY(-10px)";
      setTimeout(() => {
        alert.remove();
      }, 300);
    }, 5000);
  });

  // テーブルのソート機能（簡単な実装）
  const table = document.querySelector("table");
  if (table) {
    const headers = table.querySelectorAll("th");
    headers.forEach(function (header, index) {
      header.classList.add(
        "cursor-pointer",
        "hover:bg-gray-100",
        "transition-colors"
      );
      header.addEventListener("click", function () {
        sortTable(table, index);
      });
    });
  }

  // アニメーション効果
  const cards = document.querySelectorAll(".bg-white");
  cards.forEach((card, index) => {
    card.style.opacity = "0";
    card.style.transform = "translateY(20px)";
    setTimeout(() => {
      card.style.transition = "all 0.5s ease";
      card.style.opacity = "1";
      card.style.transform = "translateY(0)";
    }, index * 100);
  });
});

// テーブルソート関数
function sortTable(table, column) {
  const tbody = table.querySelector("tbody");
  const rows = Array.from(tbody.querySelectorAll("tr"));

  rows.sort(function (a, b) {
    const aText = a.cells[column].textContent.trim();
    const bText = b.cells[column].textContent.trim();
    return aText.localeCompare(bText);
  });

  rows.forEach(function (row) {
    tbody.appendChild(row);
  });
}

// ユーティリティ関数
function showLoading(element) {
  element.innerHTML = '<span class="loading"></span> 処理中...';
  element.disabled = true;
}

function hideLoading(element, originalText) {
  element.innerHTML = originalText;
  element.disabled = false;
}
