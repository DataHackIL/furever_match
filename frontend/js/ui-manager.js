// frontend/js/ui-manager.js
// Manages UI updates and interactions

class UIManager {
    constructor() {
        this.currentRequestId = null;
        this.currentMatches = [];
        this.init();
    }

    init() {
        // Set up event listeners
        this.setupNavigation();
        this.setupFormListeners();
        this.setupModalListeners();
    }

    /**
     * Set up navigation between pages
     */
    setupNavigation() {
        document.getElementById('nav-home').addEventListener('click', () => this.showPage('home-page'));
        document.getElementById('nav-form').addEventListener('click', () => this.showPage('form-page'));
        document.getElementById('nav-dogs').addEventListener('click', () => this.showPage('dogs-page'));
        document.getElementById('nav-matches').addEventListener('click', () => this.showPage('matches-page'));
        document.getElementById('start-btn').addEventListener('click', () => this.showPage('form-page'));
    }

    /**
     * Show a specific page
     * @param {string} pageId - Page ID to show
     */
    showPage(pageId) {
        // Hide all pages
        document.querySelectorAll('.page').forEach(page => {
            page.classList.remove('active');
        });

        // Show selected page
        const page = document.getElementById(pageId);
        if (page) {
            page.classList.add('active');
        }

        // Update active nav button
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.classList.remove('active');
        });

        const navMap = {
            'home-page': 'nav-home',
            'form-page': 'nav-form',
            'dogs-page': 'nav-dogs',
            'matches-page': 'nav-matches'
        };

        const activeBtn = document.getElementById(navMap[pageId]);
        if (activeBtn) {
            activeBtn.classList.add('active');
        }

        // Load data for specific pages
        if (pageId === 'dogs-page') {
            this.loadDogs();
        } else if (pageId === 'matches-page') {
            this.loadMatches();
        }
    }

    /**
     * Set up form listeners
     */
    setupFormListeners() {
        const form = document.getElementById('adoption-form');
        const hasKidsSelect = document.getElementById('has_kids');
        const hasOtherPetsSelect = document.getElementById('has_other_pets');

        // Show/hide conditional fields
        hasKidsSelect.addEventListener('change', (e) => {
            const kidsAgeGroup = document.getElementById('kids-age-group');
            kidsAgeGroup.style.display = e.target.value === 'yes' ? 'block' : 'none';
        });

        hasOtherPetsSelect.addEventListener('change', (e) => {
            const petsGroup = document.getElementById('which-pets-group');
            petsGroup.style.display = e.target.value === 'yes' ? 'block' : 'none';
        });

        // Handle form submission
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            await this.handleFormSubmit(form);
        });
    }

    /**
     * Handle adoption form submission
     * @param {HTMLFormElement} form - The form element
     */
    async handleFormSubmit(form) {
        this.showLoading(true);

        try {
            const formData = new FormData(form);
            const adoptionData = adoptionService.formatFormData(formData);

            const result = await adoptionService.submitForm(adoptionData);

            if (result.success) {
                this.currentRequestId = result.requestId;
                this.showSuccess('בקשתך התקבלה! עכשיו נחפש לך התאמות...');
                form.reset();

                // Load matches after successful submission
                setTimeout(() => {
                    this.loadMatches();
                    this.showPage('matches-page');
                }, 1500);
            } else {
                this.showError(result.message);
            }
        } catch (error) {
            console.error('Error submitting form:', error);
            this.showError('שגיאה בעת שליחת הבקשה');
        } finally {
            this.showLoading(false);
        }
    }

    /**
     * Load and display all dogs
     */
    async loadDogs() {
        this.showLoading(true);

        try {
            const dogs = await matchingService.getAllDogs();
            this.displayDogs(dogs);
        } catch (error) {
            console.error('Error loading dogs:', error);
            this.showError('שגיאה בטעינת הכלבים');
        } finally {
            this.showLoading(false);
        }
    }

    /**
     * Display dogs grid
     * @param {Array} dogs - Array of dogs
     */
    displayDogs(dogs) {
        const dogsList = document.getElementById('dogs-list');

        if (!dogs || dogs.length === 0) {
            dogsList.innerHTML = '<p style="grid-column: 1/-1; text-align: center;">אין כלבים זמינים כרגע</p>';
            return;
        }

        dogsList.innerHTML = dogs.map(dog => `
            <div class="dog-card" onclick="uiManager.showDogDetails('${dog.id}')">
                <div class="dog-card-image">🐕</div>
                <div class="dog-card-content">
                    <h3>${dog.name || 'Dog'}</h3>
                    <p><strong>גזע:</strong> ${dog.breed || 'Unknown'}</p>
                    <p><strong>גודל:</strong> ${dog.size || 'Unknown'}</p>
                    <p><strong>גיל:</strong> ${dog.age || 'Unknown'}</p>
                    <p><strong>מין:</strong> ${dog.gender || 'Unknown'}</p>
                    <button class="btn btn-primary" style="width: 100%; margin-top: 1rem;">
                        צפה בפרטים
                    </button>
                </div>
            </div>
        `).join('');
    }

    /**
     * Load and display matches
     */
    async loadMatches() {
        if (!this.currentRequestId) {
            document.getElementById('matches-list').innerHTML =
                '<p style="grid-column: 1/-1; text-align: center;">אנא מלא את טופס בקשת האימוץ תחילה</p>';
            return;
        }

        this.showLoading(true);

        try {
            const matches = await matchingService.getMatches(this.currentRequestId);
            this.currentMatches = matches;
            this.displayMatches(matches);
        } catch (error) {
            console.error('Error loading matches:', error);
            this.showError('שגיאה בטעינת ההתאמות');
        } finally {
            this.showLoading(false);
        }
    }

    /**
     * Display matches grid
     * @param {Array} matches - Array of match results
     */
    displayMatches(matches) {
        const matchesList = document.getElementById('matches-list');

        if (!matches || matches.length === 0) {
            matchesList.innerHTML = '<p style="grid-column: 1/-1; text-align: center;">לא נמצאו התאמות</p>';
            return;
        }

        matchesList.innerHTML = matches.map(match => {
            const formatted = matchingService.formatMatch(match);
            return `
                <div class="match-card" onclick="uiManager.showMatchDetails('${match.dog_id}')">
                    <div class="match-card-image">${formatted.quality_emoji}</div>
                    <div class="match-card-content">
                        <h3>${formatted.dog_name}</h3>
                        <p><strong>גזע:</strong> ${formatted.breed}</p>
                        <p><strong>גודל:</strong> ${formatted.size}</p>
                        <div class="match-score ${formatted.quality_class}">
                            ${formatted.match_score_display} - ${formatted.quality_label}
                        </div>
                        <button class="btn btn-primary" style="width: 100%;">
                            צפה בפרטים
                        </button>
                    </div>
                </div>
            `;
        }).join('');
    }

    /**
     * Show dog details modal
     * @param {string} dogId - Dog ID
     */
    async showDogDetails(dogId) {
        this.showLoading(true);

        try {
            const dog = await matchingService.getDog(dogId);

            if (dog) {
                const modal = document.getElementById('dog-modal');
                const details = document.getElementById('dog-details');

                details.innerHTML = `
                    <h2>${dog.name}</h2>
                    <p><strong>גזע:</strong> ${dog.breed || 'Unknown'}</p>
                    <p><strong>גיל:</strong> ${dog.age || 'Unknown'}</p>
                    <p><strong>גודל:</strong> ${dog.size || 'Unknown'}</p>
                    <p><strong>מין:</strong> ${dog.gender || 'Unknown'}</p>
                    <p><strong>רמת אילוף:</strong> ${dog.level_of_training || 'Unknown'}</p>
                    <p><strong>תיאור:</strong> ${dog.description || 'No description available'}</p>
                    <h4>התאימות:</h4>
                    <p><strong>עם ילדים:</strong> ${dog.get_along_with_kids ? 'כן' : 'לא'}</p>
                    <p><strong>עם כלבים:</strong> ${dog.get_along_with_dogs ? 'כן' : 'לא'}</p>
                    <p><strong>עם חתולים:</strong> ${dog.get_along_with_cats ? 'כן' : 'לא'}</p>
                `;

                modal.classList.add('show');
            }
        } catch (error) {
            console.error('Error loading dog details:', error);
            this.showError('שגיאה בטעינת פרטי הכלב');
        } finally {
            this.showLoading(false);
        }
    }

    /**
     * Show match details modal
     * @param {string} dogId - Dog ID
     */
    async showMatchDetails(dogId) {
        const match = this.currentMatches.find(m => m.dog_id === dogId);

        if (match) {
            const formatted = matchingService.formatMatch(match);
            const modal = document.getElementById('dog-modal');
            const details = document.getElementById('dog-details');

            let detailsHTML = `
                <h2>${formatted.dog_name}</h2>
                <div class="match-score ${formatted.quality_class}">
                    ${formatted.match_score_display} - ${formatted.quality_label}
                </div>
                <p><strong>גזע:</strong> ${formatted.breed}</p>
                <p><strong>גיל:</strong> ${formatted.age}</p>
                <p><strong>גודל:</strong> ${formatted.size}</p>
                <p><strong>מין:</strong> ${formatted.gender}</p>
            `;

            if (formatted.match_details) {
                detailsHTML += '<h4>פירוט ההתאמה:</h4><ul>';
                for (const [key, value] of Object.entries(formatted.match_details)) {
                    const displayKey = key.replace(/_/g, ' ').charAt(0).toUpperCase() + key.slice(1);
                    detailsHTML += `<li>${displayKey}: ${value}%</li>`;
                }
                detailsHTML += '</ul>';
            }

            details.innerHTML = detailsHTML;
            modal.classList.add('show');
        }
    }

    /**
     * Set up modal listeners
     */
    setupModalListeners() {
        const modal = document.getElementById('dog-modal');
        const closeBtn = modal.querySelector('.close');

        closeBtn.addEventListener('click', () => {
            modal.classList.remove('show');
        });

        window.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.classList.remove('show');
            }
        });
    }

    /**
     * Show loading indicator
     * @param {boolean} show - Show or hide
     */
    showLoading(show) {
        const loading = document.getElementById('loading');
        loading.style.display = show ? 'flex' : 'none';
    }

    /**
     * Show error message
     * @param {string} message - Error message
     */
    showError(message) {
        const errorDiv = document.getElementById('error-message');
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';

        setTimeout(() => {
            errorDiv.style.display = 'none';
        }, 5000);
    }

    /**
     * Show success message
     * @param {string} message - Success message
     */
    showSuccess(message) {
        const successDiv = document.getElementById('success-message');
        successDiv.textContent = message;
        successDiv.style.display = 'block';

        setTimeout(() => {
            successDiv.style.display = 'none';
        }, 5000);
    }
}

// Create global instance
const uiManager = new UIManager();
