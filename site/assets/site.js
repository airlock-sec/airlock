/* Airlock documentation site (task 8.6). No dependencies, no network.
   Everything here is an enhancement: the pages read and link without it. */
"use strict";

document.documentElement.classList.remove("no-js");

function copyText(text) {
  if (navigator.clipboard && window.isSecureContext) {
    return navigator.clipboard.writeText(text);
  }
  return Promise.reject(new Error("clipboard unavailable"));
}

function selectText(target) {
  var range = document.createRange();
  range.selectNodeContents(target);
  var selection = window.getSelection();
  selection.removeAllRanges();
  selection.addRange(range);
}

document.querySelectorAll("[data-copy]").forEach(function (button) {
  button.addEventListener("click", function () {
    var target = document.getElementById(button.getAttribute("data-copy"));
    if (!target) {
      return;
    }
    var label = button.textContent;
    copyText(target.innerText.replace(/\s+$/, "")).then(
      function () {
        button.textContent = "COPIED";
        button.setAttribute("data-state", "ok");
      },
      function () {
        selectText(target);
        button.textContent = "SELECT AND COPY";
        button.setAttribute("data-state", "fail");
      }
    );
    window.setTimeout(function () {
      button.textContent = label;
      button.removeAttribute("data-state");
    }, 1800);
  });
});

var list = document.getElementById("rule-list");
var search = document.getElementById("rule-filter");
var summary = document.getElementById("rule-summary");
var severityButtons = Array.prototype.slice.call(
  document.querySelectorAll("[data-severity-filter]")
);

if (list && search && summary && severityButtons.length) {
  var total = list.querySelectorAll(".rule").length;
  var severity = "all";

  var apply = function () {
    var query = search.value.trim().toLowerCase();
    var shown = 0;
    list.querySelectorAll(".family").forEach(function (family) {
      var visible = 0;
      family.querySelectorAll(".rule").forEach(function (rule) {
        var text = (rule.id + " " + rule.textContent).toLowerCase();
        var matchesSeverity =
          severity === "all" || rule.getAttribute("data-severity") === severity;
        var matchesQuery = query === "" || text.indexOf(query) !== -1;
        var match = matchesSeverity && matchesQuery;
        rule.hidden = !match;
        if (match) {
          visible += 1;
        }
      });
      family.hidden = visible === 0;
      shown += visible;
    });
    summary.textContent = shown + " OF " + total + " RULES";
  };

  search.addEventListener("input", apply);

  severityButtons.forEach(function (button) {
    button.addEventListener("click", function () {
      severity = button.getAttribute("data-severity-filter");
      severityButtons.forEach(function (other) {
        other.setAttribute("aria-pressed", String(other === button));
      });
      apply();
    });
  });

  apply();
}
