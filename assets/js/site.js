(function initializeSite() {
  "use strict";

  const root = document.documentElement;
  const language = root.lang === "zh-CN" ? "zh" : "en";
  const themeButton = document.querySelector("[data-theme-toggle]");
  const menuButton = document.querySelector("[data-menu-toggle]");
  const navigation = document.querySelector("[data-navigation]");

  function setTheme(theme) {
    root.dataset.theme = theme;
    if (themeButton) {
      const nextLabel = language === "zh" ? "切换配色" : "Change color theme";
      themeButton.setAttribute("aria-label", nextLabel);
      themeButton.setAttribute("aria-pressed", String(theme === "dark"));
    }
  }

  function getInitialTheme() {
    const savedTheme = window.localStorage.getItem("site-theme");
    if (savedTheme === "light" || savedTheme === "dark") {
      return savedTheme;
    }
    return window.matchMedia("(prefers-color-scheme: dark)").matches
      ? "dark"
      : "light";
  }

  if (themeButton) {
    setTheme(getInitialTheme());
    themeButton.addEventListener("click", function toggleTheme() {
      const nextTheme = root.dataset.theme === "dark" ? "light" : "dark";
      window.localStorage.setItem("site-theme", nextTheme);
      setTheme(nextTheme);
    });
  }

  if (menuButton && navigation) {
    menuButton.addEventListener("click", function toggleMenu() {
      const isOpen = menuButton.getAttribute("aria-expanded") === "true";
      menuButton.setAttribute("aria-expanded", String(!isOpen));
      navigation.dataset.open = String(!isOpen);
    });

    navigation.addEventListener("click", function closeMenu(event) {
      if (event.target.closest("a")) {
        menuButton.setAttribute("aria-expanded", "false");
        navigation.dataset.open = "false";
      }
    });
  }

  function createUpdateCard(update) {
    const article = document.createElement("article");
    article.className = "update-card reveal";

    const meta = document.createElement("div");
    meta.className = "update-card__meta";

    const time = document.createElement("time");
    time.dateTime = update.date;
    time.textContent = update.date.replaceAll("-", ".");

    const category = document.createElement("span");
    category.textContent = update.category[language];
    meta.append(time, category);

    const title = document.createElement("h3");
    title.textContent = update.title[language];

    const summary = document.createElement("p");
    summary.textContent = update.summary[language];

    article.append(meta, title, summary);

    if (update.url) {
      const link = document.createElement("a");
      link.href = update.url;
      link.target = "_blank";
      link.rel = "noreferrer";
      link.className = "text-link";
      link.textContent =
        language === "zh" ? "查看相关内容 ↗" : "View related item ↗";
      article.append(link);
    }

    return article;
  }

  function renderUpdates() {
    const containers = document.querySelectorAll("[data-updates]");
    const updates = [...(window.siteContent?.updates ?? [])].sort(
      (first, second) => second.date.localeCompare(first.date),
    );

    containers.forEach(function renderContainer(container) {
      const requestedLimit = Number.parseInt(
        container.dataset.limit ?? "0",
        10,
      );
      const visibleUpdates =
        requestedLimit > 0 ? updates.slice(0, requestedLimit) : updates;
      const fragment = document.createDocumentFragment();
      visibleUpdates.forEach(function appendUpdate(update) {
        fragment.append(createUpdateCard(update));
      });
      container.replaceChildren(fragment);
    });
  }

  function renderOptionalSocialLinks() {
    const containers = document.querySelectorAll("[data-optional-socials]");
    const social = window.siteContent?.social ?? {};
    const optionalNetworks = [
      { key: "weibo", label: "Weibo" },
      { key: "x", label: "X" },
      {
        key: "xiaohongshu",
        label: language === "zh" ? "小红书" : "Xiaohongshu",
      },
    ];

    containers.forEach(function renderSocialContainer(container) {
      const fragment = document.createDocumentFragment();
      let visibleNetworkCount = 0;
      optionalNetworks.forEach(function appendNetwork(network) {
        if (!social[network.key]) return;
        const link = document.createElement("a");
        link.href = social[network.key];
        link.target = "_blank";
        link.rel = "me noreferrer";
        link.className = "social-link";
        link.textContent = `${network.label} ↗`;
        fragment.append(link);
        visibleNetworkCount += 1;
      });
      container.replaceChildren(fragment);
      container.hidden = visibleNetworkCount === 0;
    });
  }

  function initializeReveals() {
    const reducedMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)",
    ).matches;
    const elements = document.querySelectorAll(".reveal");
    if (reducedMotion || !("IntersectionObserver" in window)) {
      elements.forEach((element) => element.classList.add("is-visible"));
      return;
    }

    const observer = new IntersectionObserver(
      function revealEntries(entries) {
        entries.forEach(function revealEntry(entry) {
          if (!entry.isIntersecting) return;
          entry.target.classList.add("is-visible");
          observer.unobserve(entry.target);
        });
      },
      { threshold: 0.12 },
    );
    elements.forEach((element) => observer.observe(element));
  }

  renderUpdates();
  renderOptionalSocialLinks();
  initializeReveals();
})();
