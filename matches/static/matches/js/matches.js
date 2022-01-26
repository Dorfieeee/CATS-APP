document.addEventListener('DOMContentLoaded', () => {

    $('.button[data-target="match"]')
    .api({
        action: 'cd match',
        method: 'POST',
        headers: {'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value},
        onSuccess: function(res, el, xhr) {
            // change btn option
            if (el.attr('data-option') === 'join') {
                el.attr('data-option', 'leave')
                el.data('option', 'leave')
            } else {
                el.attr('data-option', 'join')
                el.data('option', 'join')
            }
            // update match participants count
            // cannot work if used in multiple templates
            // $(el).parent().children()[0].children[1].innerText = " " + res.data.participants
        },
    })

    let btnState = {
        onActivate: function() {
            $(this).state('flash text');
        },
        onDeactivate: function() {
            $(this).state('flash text');
        }
    }

    $('[data-option="join"]')
    .state({
        ...btnState,
        text: {
          inactive   : 'Přihlásit',
          active     : 'Odhlásit',
          //deactivate : 'Odhlásit',
          flash      : 'Provedeno!',
        }
    })

    $('[data-option="leave"]')
    .state({
        ...btnState,
        text: {
          inactive   : 'Odhlásit',
          active     : 'Přihlásit',
          //deactivate : 'Přihlásit',
          flash      : 'Provedeno!',
        }
    })

})