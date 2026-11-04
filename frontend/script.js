
const pages = {
    home: {
        title: "Главная панель",
        subtitle: "Добро пожаловать в MY AI LAB"
    },
    cifar: {
        title: "CIFAR-10",
        subtitle: "Распознавание изображений"
    },
    projects: {
        title: "Мои проекты",
        subtitle: "Портфолио выполненных работ"
    },
    code: {
        title: "Code Studio",
        subtitle: "Архив программ и кода"
    }

};
let currentProjectId = null;


function openPage(name) {
    const page = pages[name] || pages.home;

    const pageIds = {
        home: "home-page",
        cifar: "cifar-page",
        projects: "projects-page",
        code: "code-page"
};

    const selected = document.getElementById(
        pageIds[name] || "home-page"
    );

    if (!selected) {
        console.error("Страница не найдена:", name);
        return;
    }

    document.querySelectorAll(".page").forEach(item => {
        item.classList.add("hidden");
    });

    selected.classList.remove("hidden");

    document.getElementById("page-title").textContent = page.title;
    document.getElementById("page-subtitle").textContent = page.subtitle;

    document.querySelectorAll("nav a").forEach(link => {
        link.classList.toggle(
            "active",
            link.dataset.page === name
        );
    });



    if (name === "projects") {
        loadProjects();
    }
    if (name === "code") {
        loadCode();
    }
}


document.querySelectorAll("nav a").forEach(link => {
    link.addEventListener("click", event => {
        event.preventDefault();
        openPage(link.dataset.page);
    });
});

document.querySelectorAll("[data-open]").forEach(card => {
    card.addEventListener("click", () => {
        openPage(card.dataset.open);
    });
});


// CIFAR-10: выбор изображения

const imageInput = document.getElementById("image-input");
const preview = document.getElementById("image-preview");
const previewContainer = document.getElementById("preview-container");
const predictButton = document.getElementById("predict-button");

let selectedFile = null;

if (imageInput) {
    imageInput.addEventListener("change", () => {
    const file = imageInput.files[0];

    document.getElementById("error-message").classList.add("hidden");
    document.getElementById("result-container").classList.add("hidden");

    if (!file) return;

    const allowedTypes = [
        "image/jpeg",
        "image/png",
        "image/webp"
    ];

    if (!allowedTypes.includes(file.type)) {
        showError("Выбери изображение JPG, PNG или WEBP.");
        imageInput.value = "";
        return;
    }

    if (file.size > 10 * 1024 * 1024) {
        showError("Размер файла превышает 10 МБ.");
        imageInput.value = "";
        return;
    }

    selectedFile = file;

    preview.src = URL.createObjectURL(file);

    document.getElementById("file-name").textContent = file.name;

    previewContainer.classList.remove("hidden");
    predictButton.disabled = false;
});
}


// Отправка изображения на backend

if (predictButton) {
    predictButton.addEventListener("click", async () => {
    if (!selectedFile) return;

    const formData = new FormData();
    formData.append("file", selectedFile);

    predictButton.disabled = true;

    document.getElementById("loading").classList.remove("hidden");
    document.getElementById("result-container").classList.add("hidden");
    document.getElementById("error-message").classList.add("hidden");

    try {
        const response = await fetch("/api/cifar/predict", {
            method: "POST",
            body: formData
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Ошибка распознавания");
        }

        document.getElementById("prediction-name").textContent =
            data.prediction;

        document.getElementById("confidence").textContent =
            data.confidence + "%";

        const list = document.getElementById("probability-list");
        list.innerHTML = "";

        data.results.forEach(item => {
            const row = document.createElement("div");
            row.className = "probability-item";

            const header = document.createElement("div");
            header.className = "probability-header";

            const name = document.createElement("span");
            name.textContent = item.class;

            const percent = document.createElement("span");
            percent.textContent = item.probability + "%";

            header.append(name, percent);

            const track = document.createElement("div");
            track.className = "progress-track";

            const fill = document.createElement("div");
            fill.className = "progress-fill";
            fill.style.width = item.probability + "%";

            track.appendChild(fill);
            row.append(header, track);
            list.appendChild(row);
        });

        document.getElementById("result-container").classList.remove("hidden");

    } catch (error) {
        showError(error.message);
    } finally {
        document.getElementById("loading").classList.add("hidden");
        predictButton.disabled = false;
    }
});
}


function showError(message) {
    const element = document.getElementById("error-message");
    element.textContent = message;
    element.classList.remove("hidden");
}



// ======================================
// MY AI LAB — МОИ ПРОЕКТЫ
// ======================================


async function loadProjects() {
    const list = document.getElementById("projects-list");
    const error = document.getElementById("projects-error");

    // Возвращаем список проектов
    list.parentElement.classList.remove("hidden");
    document.getElementById("project-detail").classList.add("hidden");

    list.replaceChildren();
    error.classList.add("hidden");

    const loading = document.createElement("p");
    loading.textContent = "Загрузка проектов...";
    list.appendChild(loading);

    try {
        const response = await fetch("/api/projects");

        if (!response.ok) {
            throw new Error("Не удалось загрузить проекты");
        }

        const projects = await response.json();

        list.replaceChildren();

        if (projects.length === 0) {
            const empty = document.createElement("p");
            empty.textContent = "Пока проектов нет.";
            list.appendChild(empty);
            return;
        }

        projects.forEach(project => {
            const card = document.createElement("div");
            card.className = "project-item";
            card.dataset.projectId = project.id;

            const title = document.createElement("h3");
            title.textContent = project.title;

            card.appendChild(title);

            // Открытие проекта
            card.addEventListener("click", () => {
                openProject(project);
            });

            // Не добавляем удаление для CIFAR-10
            if (project.project_type !== "cifar") {
                const deleteButton = document.createElement("button");

                deleteButton.textContent = "Удалить проект";
                deleteButton.className = "delete-project-button";

                deleteButton.addEventListener("click", async (event) => {
                    event.stopPropagation();

                    if (!confirm(`Удалить проект «${project.title}» и все его файлы?`)) {
                        return;
                    }

                    deleteButton.disabled = true;
                    deleteButton.textContent = "Удаление...";

                    try {
                        const deleteResponse = await fetch(
                            `/api/projects/${project.id}`,
                            { method: "DELETE" }
                        );

                        const data = await deleteResponse.json();

                        if (!deleteResponse.ok) {
                            throw new Error(data.detail || "Ошибка удаления проекта");
                        }

                        await loadProjects();
                        await updateProjectsCount();

                    } catch (err) {
                        alert(err.message);
                        deleteButton.disabled = false;
                        deleteButton.textContent = "Удалить проект";
                    }
                });

                card.appendChild(deleteButton);
            }

            list.appendChild(card);
        });

    } catch (err) {
        list.replaceChildren();
        error.textContent = err.message;
        error.classList.remove("hidden");
    }
}



// Открытие отдельного проекта

function openProject(project) {
    currentProjectId = project.id;

    // CIFAR-10 открывает специальную страницу
    if (project.project_type === "cifar") {
        openPage("cifar");
        return;
    }

    document.getElementById("projects-list").parentElement
        .classList.add("hidden");

    const detail = document.getElementById("project-detail");
    detail.classList.remove("hidden");

    document.getElementById("detail-title").textContent =
        project.title;

    document.getElementById("detail-description").textContent =
        project.description || "Описание отсутствует";

    const result = document.getElementById("detail-result");
    result.textContent =
        project.result_text || "Сохранённых результатов пока нет.";

    // Создаём кнопку редактирования
    const oldButton = document.getElementById("edit-project-button");

    if (oldButton) {
        oldButton.remove();
    }

    const editButton = document.createElement("button");
    editButton.id = "edit-project-button";
    editButton.className = "edit-project-button";
    editButton.textContent = "✏️ Редактировать проект";

    editButton.addEventListener("click", () => {
        openEditProjectModal(project);
    });

    document.getElementById("detail-description")
        .insertAdjacentElement("afterend", editButton);

    loadProjectFiles();
}

// Возврат из проекта к списку проектов
document.getElementById("back-projects")
    .addEventListener("click", async () => {

        currentProjectId = null;

        // Скрываем подробности проекта
        document.getElementById("project-detail")
            .classList.add("hidden");

        // Показываем список проектов
        document.getElementById("projects-list").parentElement
            .classList.remove("hidden");

        // Сбрасываем выбранный файл
        projectFileInput.value = "";
        uploadProjectFileButton.disabled = true;
        uploadProjectFileButton.textContent = "Загрузить в проект";

        // Обновляем список проектов
        await loadProjects();
    });

// Окно редактирования проекта
function openEditProjectModal(project) {
    // Создаём затемнение
    const modal = document.createElement("div");
    modal.className = "edit-project-modal";

    // Панель окна
    const panel = document.createElement("div");
    panel.className = "edit-project-panel";

    const heading = document.createElement("h2");
    heading.textContent = "Редактирование проекта";

    // Поле названия
    const titleLabel = document.createElement("label");
    titleLabel.textContent = "Название проекта";

    const titleInput = document.createElement("input");
    titleInput.type = "text";
    titleInput.value = project.title;
    titleInput.placeholder = "Введите название проекта";

    // Поле описания
    const descriptionLabel = document.createElement("label");
    descriptionLabel.textContent = "Описание проекта";

    const descriptionInput = document.createElement("textarea");
    descriptionInput.value = project.description || "";
    descriptionInput.placeholder = "Расскажите о проекте...";
    descriptionInput.rows = 5;

    // Сообщение об ошибке
    const error = document.createElement("p");
    error.className = "edit-project-error hidden";

    // Кнопки
    const actions = document.createElement("div");
    actions.className = "edit-project-actions";

    const cancelButton = document.createElement("button");
    cancelButton.textContent = "Отмена";
    cancelButton.className = "edit-cancel-button";

    const saveButton = document.createElement("button");
    saveButton.textContent = "Сохранить";
    saveButton.className = "edit-save-button";

    // Закрытие окна
    cancelButton.addEventListener("click", () => {
        modal.remove();
    });

    modal.addEventListener("click", (event) => {
        if (event.target === modal) {
            modal.remove();
        }
    });

    // Сохранение изменений
    saveButton.addEventListener("click", async () => {
        const title = titleInput.value.trim();
        const description = descriptionInput.value.trim();

        if (!title) {
            error.textContent = "Введите название проекта";
            error.classList.remove("hidden");
            return;
        }

        saveButton.disabled = true;
        saveButton.textContent = "Сохранение...";
        error.classList.add("hidden");

        try {
            const response = await fetch(
                `/api/projects/${project.id}`,
                {
                    method: "PUT",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        title: title,
                        description: description
                    })
                }
            );

            const data = await response.json();

            if (!response.ok) {
                throw new Error(
                    data.detail || "Не удалось сохранить проект"
                );
            }

            // Обновляем данные проекта
            project.title = data.title;
            project.description = data.description;

            // Обновляем страницу проекта
            document.getElementById("detail-title").textContent =
                data.title;

            document.getElementById("detail-description").textContent =
                data.description || "Описание отсутствует";

            // Обновляем название в списке проектов
            const projectCard = document.querySelector(
                `[data-project-id="${project.id}"] h3`
            );

            if (projectCard) {
                projectCard.textContent = data.title;
            }

            modal.remove();

        } catch (err) {
            error.textContent = err.message;
            error.classList.remove("hidden");

            saveButton.disabled = false;
            saveButton.textContent = "Сохранить";
        }
    });

    // Собираем окно
    actions.append(cancelButton, saveButton);

    panel.append(
        heading,
        titleLabel,
        titleInput,
        descriptionLabel,
        descriptionInput,
        error,
        actions
    );

    modal.appendChild(panel);
    document.body.appendChild(modal);

    titleInput.focus();
}

// ======================================
// СОЗДАНИЕ НОВОГО ПРОЕКТА
// ======================================

const createProjectButton = document.getElementById("create-project-button");
const createProjectForm = document.getElementById("create-project-form");
const cancelProjectButton = document.getElementById("cancel-project");
const createProjectError = document.getElementById("create-project-error");

// Открытие формы
createProjectButton.addEventListener("click", () => {
    createProjectForm.classList.remove("hidden");
    createProjectButton.classList.add("hidden");
    createProjectError.classList.add("hidden");

    document.getElementById("project-title").focus();
});

// Отмена создания
cancelProjectButton.addEventListener("click", () => {
    createProjectForm.reset();
    createProjectForm.classList.add("hidden");
    createProjectButton.classList.remove("hidden");
    createProjectError.classList.add("hidden");
});

// Сохранение проекта
createProjectForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const title = document.getElementById("project-title").value.trim();
    const description = document.getElementById("project-description").value.trim();

    if (!title) {
        createProjectError.textContent = "Введите название проекта.";
        createProjectError.classList.remove("hidden");
        return;
    }

    const submitButton = createProjectForm.querySelector(
        'button[type="submit"]'
    );

    submitButton.disabled = true;
    submitButton.textContent = "Сохранение...";
    createProjectError.classList.add("hidden");

    try {
        const response = await fetch("/api/projects", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                title: title,
                description: description
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Не удалось создать проект");
        }

        // Очищаем и закрываем форму
        createProjectForm.reset();
        createProjectForm.classList.add("hidden");
        createProjectButton.classList.remove("hidden");

        // Обновляем список проектов
        await loadProjects();

        // Обновляем счётчик на главной странице
        await updateProjectsCount();

    } catch (error) {
        createProjectError.textContent = error.message;
        createProjectError.classList.remove("hidden");
    } finally {
        submitButton.disabled = false;
        submitButton.textContent = "Сохранить проект";
    }
});


// Обновление количества проектов на главной
async function updateProjectsCount() {
    try {
        const response = await fetch("/api/projects");

        if (!response.ok) {
            throw new Error("Не удалось получить проекты");
        }

        const projects = await response.json();

        const counter = document.querySelector(
            "#home-page .stats .card:first-child h2"
        );

        if (counter) {
    counter.textContent = projects.length;
}

    } catch (error) {
        console.error("Ошибка обновления счётчика:", error);
    }
}
updateProjectsCount();


 // ======================================
 // ЗАГРУЗКА И ОТОБРАЖЕНИЕ ФАЙЛОВ ПРОЕКТА
 // ======================================

const projectFileInput = document.getElementById("project-file-input");
const uploadProjectFileForm = document.getElementById("upload-project-file-form");
const uploadProjectFileButton = document.getElementById("upload-project-file-button");
const projectFilesList = document.getElementById("project-files-list");
const uploadFileError = document.getElementById("upload-file-error");

const MAX_PROJECT_FILE_SIZE = 20 * 1024 * 1024;

// Выбор файла
projectFileInput.addEventListener("change", () => {
    const file = projectFileInput.files[0];

    uploadFileError.classList.add("hidden");

    if (!file) {
        uploadProjectFileButton.disabled = true;
        return;
    }

    if (file.size > MAX_PROJECT_FILE_SIZE) {
        uploadFileError.textContent = "Файл превышает 20 МБ.";
        uploadFileError.classList.remove("hidden");
        projectFileInput.value = "";
        uploadProjectFileButton.disabled = true;
        return;
    }

    uploadProjectFileButton.disabled = false;
    uploadProjectFileButton.textContent = "Загрузить: " + file.name;
});


// Отправка файла на сервер
uploadProjectFileForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    if (!currentProjectId) {
        uploadFileError.textContent = "Сначала открой проект.";
        uploadFileError.classList.remove("hidden");
        return;
    }

    const file = projectFileInput.files[0];

    if (!file) {
        uploadFileError.textContent = "Сначала выбери файл.";
        uploadFileError.classList.remove("hidden");
        return;
    }

    const formData = new FormData();
    formData.append("file", file);

    uploadProjectFileButton.disabled = true;
    uploadProjectFileButton.textContent = "Загрузка...";
    uploadFileError.classList.add("hidden");

    try {
        const response = await fetch(
            `/api/projects/${currentProjectId}/files`,
            {
                method: "POST",
                body: formData
            }
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Ошибка загрузки файла");
        }

        projectFileInput.value = "";
        uploadProjectFileButton.textContent = "Загрузить в проект";

        await loadProjectFiles();

    } catch (error) {
        uploadFileError.textContent = error.message;
        uploadFileError.classList.remove("hidden");
    } finally {
        uploadProjectFileButton.disabled = true;
        uploadProjectFileButton.textContent = "Загрузить в проект";
    }
});


// Получение списка файлов проекта

async function loadProjectFiles() {
    if (!currentProjectId) return;

    projectFilesList.replaceChildren();

    const loading = document.createElement("p");
    loading.textContent = "Загрузка файлов...";
    projectFilesList.appendChild(loading);

    try {
        const response = await fetch(
            `/api/projects/${currentProjectId}/files`
        );

        const files = await response.json();

        if (!response.ok) {
            throw new Error(files.detail || "Не удалось получить файлы");
        }

        projectFilesList.replaceChildren();

        uploadProjectFileForm.classList.toggle(
            "hidden",
            files.length > 0
        );

        if (files.length === 0) {
            const empty = document.createElement("p");
            empty.textContent = "В этом проекте пока нет файлов.";
            projectFilesList.appendChild(empty);
            return;
        }

        files.forEach(file => {
            const card = document.createElement("div");
            card.className = "project-file-item";

            // Получаем расширение файла
            const extension = file.original_name
                .split(".")
                .pop()
                .toUpperCase();

            // Форматируем размер
            function formatFileSize(bytes) {
                if (bytes < 1024) {
                    return bytes + " Б";
                }

                if (bytes < 1024 * 1024) {
                    return (bytes / 1024).toFixed(1) + " КБ";
                }

                return (bytes / (1024 * 1024)).toFixed(2) + " МБ";
            }

            // Верхняя часть карточки
            const header = document.createElement("div");
            header.className = "project-file-header";

            const icon = document.createElement("div");
            icon.className = "project-file-icon";
            icon.textContent = extension === "PDF" ? "📕" :
                ["PNG", "JPG", "JPEG", "WEBP", "GIF"].includes(extension) ? "🖼️" :
                ["DOC", "DOCX", "TXT"].includes(extension) ? "📄" :
                ["XLS", "XLSX", "CSV"].includes(extension) ? "📊" :
                ["PPT", "PPTX"].includes(extension) ? "📽️" :
                extension === "ZIP" ? "📦" : "📁";

            const info = document.createElement("div");
            info.className = "project-file-info";

            const name = document.createElement("h4");
            name.textContent = file.original_name;

            const details = document.createElement("p");
            details.className = "project-file-details";

            const date = new Date(file.created_at);

const formattedDate = isNaN(date.getTime())
    ? "Дата неизвестна"
    : date.toLocaleString("ru-RU");

details.textContent =
    `${extension} • ${formatFileSize(file.size || 0)} • ${formattedDate}`;

            info.append(name, details);
            header.append(icon, info);
            card.appendChild(header);

            // Предпросмотр изображения
            if (file.mime_type && file.mime_type.startsWith("image/")) {
                const image = document.createElement("img");
                image.src = file.image_url;
                image.alt = file.original_name;
                image.className = "project-file-image";
                card.appendChild(image);
            }

            // Кнопки действий
            const actions = document.createElement("div");
            actions.className = "project-file-actions";

            if (file.mime_type && file.mime_type.startsWith("image/")) {
                const view = document.createElement("a");
                view.href = file.image_url;
                view.target = "_blank";
                view.rel = "noopener noreferrer";
                view.textContent = "Просмотреть";
                view.className = "view-file-button";
                actions.appendChild(view);
            }

            const download = document.createElement("a");
            download.href = file.download_url;
            download.textContent = "Скачать";
            download.download = file.original_name;
            download.className = "download-file-link";
            actions.appendChild(download);

            const deleteButton = document.createElement("button");
            deleteButton.textContent = "Удалить";
            deleteButton.className = "delete-file-button";

            deleteButton.addEventListener("click", async () => {
                if (!confirm("Удалить этот файл?")) return;

                deleteButton.disabled = true;

                try {
                    const deleteResponse = await fetch(
                        `/api/files/${file.id}`,
                        { method: "DELETE" }
                    );

                    const data = await deleteResponse.json();

                    if (!deleteResponse.ok) {
                        throw new Error(data.detail || "Ошибка удаления");
                    }

                    await loadProjectFiles();

                } catch (error) {
                    alert(error.message);
                    deleteButton.disabled = false;
                }
            });

            actions.appendChild(deleteButton);
            card.appendChild(actions);

            projectFilesList.appendChild(card);
        });

    } catch (error) {
        projectFilesList.replaceChildren();

        const message = document.createElement("p");
        message.textContent = "Ошибка: " + error.message;
        projectFilesList.appendChild(message);
    }
}



// ======================================
// MY AI LAB — CODE STUDIO
// ======================================

let currentCodeId = null;
let currentCode = null;

// Открытие формы добавления программы
const addCodeButton = document.getElementById("add-code-button");

if (addCodeButton) {
    addCodeButton.addEventListener("click", async () => {
        const error = document.getElementById("code-form-error");

        try {
            currentCodeId = null;
            currentCode = null;

            document.getElementById("code-form").reset();

            document.getElementById("code-form-title").textContent =
                "Новая программа";

            error.classList.add("hidden");

            await loadCodeProjects();

            document.getElementById("code-list-section").classList.add("hidden");
            document.getElementById("code-detail-section").classList.add("hidden");
            document.getElementById("code-form-section").classList.remove("hidden");

            document.getElementById("code-content").focus();

        } catch (err) {
            error.textContent = err.message;
            error.classList.remove("hidden");
        }
    });
} else {
    console.error("Кнопка add-code-button не найдена");
}



// Загрузка всех программ
async function loadCode() {
    const list = document.getElementById("code-list");
    const error = document.getElementById("code-list-error");

    document.getElementById("code-list-section").classList.remove("hidden");
    document.getElementById("code-form-section").classList.add("hidden");
    document.getElementById("code-detail-section").classList.add("hidden");

    list.replaceChildren();
    error.classList.add("hidden");

    try {
        const response = await fetch("/api/code");
        const codes = await response.json();

        if (!response.ok) {
            throw new Error(codes.detail || "Не удалось загрузить код");
        }

        list.replaceChildren();

        if (codes.length === 0) {
            const empty = document.createElement("p");
            empty.textContent = "Пока нет сохранённого кода.";
            list.appendChild(empty);
        }

        codes.forEach(item => {
            const card = document.createElement("div");
            card.className = "project-item";

            const title = document.createElement("h3");
            title.textContent = item.project_title;

            const info = document.createElement("p");
            info.textContent = `Язык программирования: ${item.language.toUpperCase()}`;

            card.append(title, info);

            card.addEventListener("click", () => {
                openCode(item.id);
            });

            list.appendChild(card);
        });

        updateCodeCount(codes.length);

    } catch (err) {
        list.replaceChildren();
        error.textContent = err.message;
        error.classList.remove("hidden");
    }
}

// Обновление счётчика программ на главной
async function updateCodeCount(count = null) {
    try {
        if (count === null) {
            const response = await fetch("/api/code");
            if (!response.ok) return;

            const codes = await response.json();
            count = codes.length;
        }

        const counter = document.querySelector(
            "#home-page .stats .card:nth-child(2) h2"
        );

        if (counter) {
            counter.textContent = count;
        }

    } catch (error) {
        console.error("Ошибка обновления количества программ:", error);
    }
}


// Заполнение списка проектов
async function loadCodeProjects(selectedId = null) {
    const select = document.getElementById("code-project");

    select.disabled = false;
    select.replaceChildren();

    const placeholder = document.createElement("option");
    placeholder.value = "";
    placeholder.textContent = "Выбери проект";
    select.appendChild(placeholder);

    const response = await fetch("/api/projects");

    if (!response.ok) {
        throw new Error("Не удалось загрузить проекты");
    }

    const projects = await response.json();

    const availableProjects = projects.filter(
        project => project.project_type !== "cifar"
    );

    if (availableProjects.length === 0) {
        placeholder.textContent = "Сначала создай проект";
        select.disabled = true;
        return;
    }

    availableProjects.forEach(project => {
        const option = document.createElement("option");
        option.value = project.id;
        option.textContent = project.title;

        if (String(project.id) === String(selectedId)) {
            option.selected = true;
        }

        select.appendChild(option);
    });
}

// Отмена формы
function closeCodeForm() {
    document.getElementById("code-form").reset();

    document.getElementById("code-project").disabled = false;

    document.getElementById("code-form-section").classList.add("hidden");
    document.getElementById("code-list-section").classList.remove("hidden");

    document.getElementById("code-form-error").classList.add("hidden");

    currentCodeId = null;
    currentCode = null;
}

document.getElementById("cancel-code-form")
    .addEventListener("click", closeCodeForm);

document.getElementById("cancel-code-button")
    .addEventListener("click", closeCodeForm);


// Сохранение кода, прикреплённого к проекту
document.getElementById("code-form").addEventListener("submit", async event => {
    event.preventDefault();

    const projectId = document.getElementById("code-project").value;
    const language = document.getElementById("code-language").value;
    const code = document.getElementById("code-content").value;

    const error = document.getElementById("code-form-error");
    const submitButton = event.currentTarget.querySelector(
        'button[type="submit"]'
    );

    error.classList.add("hidden");

    if (!projectId || !code.trim()) {
        error.textContent = "Выбери проект и добавь исходный код.";
        error.classList.remove("hidden");
        return;
    }

    const projectSelect = document.getElementById("code-project");
    const projectName = projectSelect.options[
        projectSelect.selectedIndex
    ].textContent;

    const payload = {
        title: projectName,
        language: language,
        filename: "",
        code: code
    };

    let url = "/api/code";
    let method = "POST";

    if (currentCodeId !== null) {
        url = `/api/code/${currentCodeId}`;
        method = "PUT";
    } else {
        payload.project_id = Number(projectId);
    }

    submitButton.disabled = true;
    submitButton.textContent = "Сохранение...";

    try {
        const response = await fetch(url, {
            method: method,
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(payload)
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Не удалось сохранить код");
        }

        closeCodeForm();
        await loadCode();
        await updateCodeCount();

    } catch (err) {
        error.textContent = err.message;
        error.classList.remove("hidden");

    } finally {
        submitButton.disabled = false;
        submitButton.textContent = "Сохранить программу";
    }
});

// Открытие программы
async function openCode(codeId) {
    try {
        const response = await fetch(`/api/code/${codeId}`);
        const item = await response.json();

        if (!response.ok) {
            throw new Error(item.detail || "Не удалось открыть программу");
        }

        currentCodeId = item.id;
        currentCode = item;

        document.getElementById("code-list-section").classList.add("hidden");
        document.getElementById("code-form-section").classList.add("hidden");
        document.getElementById("code-detail-section").classList.remove("hidden");

        const codeElement = document.getElementById("code-detail-content");

// Устанавливаем язык программирования
const language = item.language.toLowerCase();

const supportedLanguages = [
    "python",
    "javascript",
    "java",
    "sql",
    "cpp"
];

codeElement.className = supportedLanguages.includes(language)
    ? `language-${language}`
    : "language-plaintext";

// Добавляем исходный код
codeElement.textContent = item.code;

// Применяем подсветку синтаксиса
if (window.hljs) {
    delete codeElement.dataset.highlighted;
    hljs.highlightElement(codeElement);
}

        document.getElementById("code-detail-info").textContent =
    `Проект: ${item.project_title}`;

        document.getElementById("code-detail-error").classList.add("hidden");

    } catch (error) {
        alert(error.message);
    }
}


// Возврат к списку программ
function backToCodeList() {
    currentCodeId = null;
    currentCode = null;
    loadCode();
}

document.getElementById("back-code-list")
    .addEventListener("click", backToCodeList);


// Копирование исходного кода
document.getElementById("copy-code-button")
    .addEventListener("click", async () => {
        if (!currentCode) return;

        try {
            await navigator.clipboard.writeText(currentCode.code);

            const button = document.getElementById("copy-code-button");
            button.textContent = "Скопировано!";

            setTimeout(() => {
                button.textContent = "Копировать код";
            }, 1500);

        } catch (error) {
            alert("Не удалось скопировать код.");
        }
    });


// Редактирование кода
document.getElementById("edit-code-button")
    .addEventListener("click", async () => {
        if (!currentCode) return;

        const item = currentCode;

        document.getElementById("code-form").reset();

        document.getElementById("code-form-title").textContent =
            "Редактирование кода";

        document.getElementById("code-language").value = item.language;
        document.getElementById("code-content").value = item.code;

        document.getElementById("code-list-section").classList.add("hidden");
        document.getElementById("code-detail-section").classList.add("hidden");
        document.getElementById("code-form-section").classList.remove("hidden");

        document.getElementById("code-form-error").classList.add("hidden");

        try {
            await loadCodeProjects(item.project_id);

            document.getElementById("code-project").disabled = true;

        } catch (error) {
            document.getElementById("code-form-error").textContent = error.message;
            document.getElementById("code-form-error").classList.remove("hidden");
        }
    });
// Удаление программы
document.getElementById("delete-code-button")
    .addEventListener("click", async () => {
        if (!currentCode) return;

        if (!confirm(`Удалить код проекта «${currentCode.project_title}»?`)) {
            return;
        }
        const button = document.getElementById("delete-code-button");
        button.disabled = true;
        button.textContent = "Удаление...";

        try {
            const response = await fetch(`/api/code/${currentCode.id}`, {
                method: "DELETE"
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || "Не удалось удалить программу");
            }

            currentCode = null;
            currentCodeId = null;

            await loadCode();
            await updateCodeCount();

        } catch (error) {
            alert(error.message);
        } finally {
            button.disabled = false;
            button.textContent = "Удалить";
        }
    });


// Переход к связанному проекту из Code Studio
document.getElementById("code-detail-info")
    .addEventListener("click", async () => {
        if (!currentCode) return;

        try {
            const response = await fetch("/api/projects");
            const projects = await response.json();

            if (!response.ok) {
                throw new Error("Не удалось загрузить проекты");
            }

            const project = projects.find(
                item => item.id === currentCode.project_id
            );

            if (!project) {
                throw new Error("Связанный проект не найден");
            }

            openPage("projects");
            openProject(project);

        } catch (error) {
            alert(error.message);
        }
    });


// Первоначальное обновление счётчика
updateCodeCount();



