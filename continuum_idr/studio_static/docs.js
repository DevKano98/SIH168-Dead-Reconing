const docArticles = [...document.querySelectorAll(".docs-content article")];
const sidebarLinks = [...document.querySelectorAll("#docs-nav a")];
const toc = document.getElementById("toc");

docArticles.forEach((article) => {
  const heading = article.querySelector("h1,h2");
  if (!heading) return;
  const link = document.createElement("a");
  link.href = `#${article.id}`;
  link.textContent = heading.textContent;
  toc.appendChild(link);
});

const tocLinks = [...toc.querySelectorAll("a")];
const observer = new IntersectionObserver((entries) => {
  const visible = entries.filter((entry) => entry.isIntersecting).sort((a,b) => a.boundingClientRect.top - b.boundingClientRect.top)[0];
  if (!visible) return;
  [...sidebarLinks, ...tocLinks].forEach((link) => link.classList.toggle("active", link.hash === `#${visible.target.id}`));
}, {rootMargin: "-15% 0px -70%", threshold: 0});
docArticles.forEach((article) => observer.observe(article));

document.querySelectorAll(".copy").forEach((button) => {
  button.addEventListener("click", async () => {
    const text = button.parentElement.querySelector("code").innerText;
    try {
      await navigator.clipboard.writeText(text);
      button.textContent = "Copied"; button.classList.add("copied");
      setTimeout(() => { button.textContent = "Copy"; button.classList.remove("copied"); }, 1400);
    } catch (_) { button.textContent = "Select code"; }
  });
});

document.getElementById("docs-search").addEventListener("input", (event) => {
  const query = event.target.value.trim().toLowerCase();
  docArticles.forEach((article) => {
    const content = `${article.dataset.search || ""} ${article.textContent}`.toLowerCase();
    article.classList.toggle("search-hidden", Boolean(query) && !content.includes(query));
  });
});

document.getElementById("mobile-menu").addEventListener("click", () => document.getElementById("docs-sidebar").classList.toggle("open"));
sidebarLinks.forEach((link) => link.addEventListener("click", () => document.getElementById("docs-sidebar").classList.remove("open")));

fetch("/api/summary").then((response) => response.ok ? response.json() : Promise.reject()).then((summary) => {
  const cards = document.querySelectorAll("#docs-results strong");
  cards[0].textContent = summary.total_outages_evaluated;
  cards[1].textContent = `${summary.overall.median_endpoint_error_m.toFixed(1)} m`;
  cards[2].textContent = `${summary.overall.median_drift_percent.toFixed(1)}%`;
  cards[3].textContent = `${(summary.overall.pass_rate_below_10_percent * 100).toFixed(0)}%`;
}).catch(() => {});
