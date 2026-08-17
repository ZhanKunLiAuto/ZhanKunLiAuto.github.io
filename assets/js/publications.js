(function initializePublications() {
  "use strict";

  const container = document.querySelector("[data-publication-list]");
  if (!container) return;

  const language = document.documentElement.lang === "zh-CN" ? "zh" : "en";
  const searchInput = document.querySelector("[data-publication-search]");
  const yearSelect = document.querySelector("[data-publication-year]");
  const count = document.querySelector("[data-publication-count]");
  let publications = [];

  const labels = {
    en: {
      citation: "citations",
      paper: "Paper",
      pdf: "PDF",
      scholar: "Scholar",
      empty: "No publications match this filter.",
      error:
        "The publication list could not be loaded. Please use Google Scholar.",
      allYears: "All years",
      shown: "publications shown",
    },
    zh: {
      citation: "次引用",
      paper: "论文页面",
      pdf: "PDF",
      scholar: "Scholar",
      empty: "没有符合当前条件的论文。",
      error: "论文列表暂时无法载入，请前往 Google Scholar 查看。",
      allYears: "全部年份",
      shown: "篇论文",
    },
  }[language];

  function createLink(label, href) {
    if (!href) return null;
    const link = document.createElement("a");
    link.href = href;
    link.target = "_blank";
    link.rel = "noreferrer";
    link.textContent = `${label} ↗`;
    return link;
  }

  function createPublication(publication, index) {
    const article = document.createElement("article");
    article.className = "publication-row";

    const number = document.createElement("span");
    number.className = "publication-row__number";
    number.textContent = String(index + 1).padStart(2, "0");

    const body = document.createElement("div");
    body.className = "publication-row__body";

    const meta = document.createElement("div");
    meta.className = "publication-row__meta";
    const year = document.createElement("span");
    year.textContent = publication.year;
    const venue = document.createElement("span");
    venue.textContent = publication.venue || "Preprint";
    meta.append(year, venue);

    const title = document.createElement("h2");
    title.textContent = publication.title;

    const authors = document.createElement("p");
    authors.className = "publication-row__authors";
    authors.textContent = publication.authors;

    const footer = document.createElement("div");
    footer.className = "publication-row__footer";
    const citations = document.createElement("span");
    citations.className = "citation-chip";
    citations.textContent = `${publication.citationCount} ${labels.citation}`;
    footer.append(citations);

    const links = [
      createLink(labels.paper, publication.externalUrl),
      createLink(labels.pdf, publication.pdfUrl),
      createLink(labels.scholar, publication.scholarUrl),
    ].filter(Boolean);
    links.forEach((link) => footer.append(link));

    body.append(meta, title, authors, footer);
    article.append(number, body);
    return article;
  }

  function render() {
    const query = searchInput?.value.trim().toLocaleLowerCase() ?? "";
    const selectedYear = yearSelect?.value ?? "";
    const filtered = publications.filter(function matches(publication) {
      const searchable =
        `${publication.title} ${publication.authors} ${publication.venue}`.toLocaleLowerCase();
      const matchesQuery = !query || searchable.includes(query);
      const matchesYear = !selectedYear || publication.year === selectedYear;
      return matchesQuery && matchesYear;
    });

    const fragment = document.createDocumentFragment();
    if (filtered.length === 0) {
      const empty = document.createElement("p");
      empty.className = "empty-state";
      empty.textContent = labels.empty;
      fragment.append(empty);
    } else {
      filtered.forEach((publication, index) => {
        fragment.append(createPublication(publication, index));
      });
    }
    container.replaceChildren(fragment);
    if (count) count.textContent = `${filtered.length} ${labels.shown}`;
  }

  function populateYears() {
    if (!yearSelect) return;
    const years = [
      ...new Set(publications.map((publication) => publication.year)),
    ].sort((first, second) => Number(second) - Number(first));
    const allYears = document.createElement("option");
    allYears.value = "";
    allYears.textContent = labels.allYears;
    yearSelect.append(allYears);
    years.forEach(function appendYear(year) {
      const option = document.createElement("option");
      option.value = year;
      option.textContent = year;
      yearSelect.append(option);
    });
  }

  fetch(container.dataset.source ?? "../data/publications.json")
    .then(function validateResponse(response) {
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return response.json();
    })
    .then(function renderPublications(payload) {
      publications = payload.publications ?? [];
      populateYears();
      render();
    })
    .catch(function showError() {
      const error = document.createElement("p");
      error.className = "empty-state";
      error.textContent = labels.error;
      container.replaceChildren(error);
    });

  searchInput?.addEventListener("input", render);
  yearSelect?.addEventListener("change", render);
})();
