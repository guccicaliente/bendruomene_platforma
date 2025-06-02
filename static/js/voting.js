// Funkcija CSRF žymos gavimui iš Django šablonų
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Balsavimo ištrynimo funkcija
window.deleteVoting = function(id, type) {
    if (confirm(`Ar tikrai norite ištrinti šį ${type} balsavimą?`)) {
        const csrfToken = getCookie('csrftoken');
        fetch(`/valdymas/balsavimai/${id}/trinti/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/json'
            },
            credentials: 'same-origin'
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP klaida! statusas: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.status === 'success') {
                window.location.reload();
            } else {
                throw new Error(data.message || 'Nepavyko ištrinti balsavimo');
            }
        })
        .catch(error => {
            console.error('Klaida:', error);
            alert('Įvyko klaida bandant ištrinti balsavimą: ' + error.message);
        });
    }
}

// Balsavimo redagavimo funkcija
window.editVoting = function(id) {
    const csrfToken = getCookie('csrftoken');
    fetch(`/valdymas/balsavimai/${id}/`, {
        headers: {
            'X-CSRFToken': csrfToken,
            'Content-Type': 'application/json'
        },
        credentials: 'same-origin'
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP klaida! statusas: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        const form = document.getElementById('editVotingForm');
        form.action = `/valdymas/balsavimai/${id}/redaguoti/`;
        
        form.querySelector('[name="title"]').value = data.title;
        form.querySelector('[name="description"]').value = data.description;
        form.querySelector('[name="end_date"]').value = data.end_date || '';
        
        new bootstrap.Modal(document.getElementById('editVotingModal')).show();
    })
    .catch(error => {
        console.error('Klaida:', error);
        alert('Nepavyko gauti balsavimo duomenų: ' + error.message);
    });
}

// Inicializacija po puslapio užkrovimo
document.addEventListener('DOMContentLoaded', function() {
    // Inicializuojame datų pasirinkimo įrankį
    flatpickr("input[type=date]", {
        dateFormat: "Y-m-d",
        minDate: "today"
    });
}); 