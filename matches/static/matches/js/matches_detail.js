document.addEventListener('DOMContentLoaded', () => {
    const PLAYER_REGEX = /^(\w+)\[(\d+)\]\[(\d+)\]$/,
          LEADER_REGEX = /^(leader)\[(\d+)\]$/,
          $FORM_TAB = $('.tab[data-tab="add round"]')
    
    initTabs()

    function initTabs() {
        $('#round-tab-menu .item[data-tab]')
            .tab({
                autoTabActivation: true,
                cache: true,
                onVisible: function (obj) {
                    let tabEl = $(this),
                        dataTab = tabEl.data('tab'),
                        dataOrder = tabEl.data('order'),
                        dataId = tabEl.data('id'),
                        round = dataOrder,
                        html = tabEl.tab('cache read', dataTab)

                    if (round) {
                        // Check cache before ajax
                        if (typeof html === 'string') {
                            tabEl.html(html)
                            return
                        }
                        // Show loading
                        tabEl.toggleClass('loading')
                        $.ajax({
                            url: 'kolo/' + round, success: function (res) {
                                let { data, success } = res
                                // success
                                if (res && success === 'true') {
                                    html = createTable(data)
                                    tabEl.html(html)
                                    tabEl.toggleClass('loading')
                                    tabEl.tab('cache add', dataTab, html)
                                }
                                // error
                            }
                        });
                    }

                    if (dataTab === 'scoreboard') {

                    }

                    if (dataTab === 'add round') {
                        if (tabEl.data('triggered')) {
                            return
                        }

                        let alertTimer = setAlert(5000)
                        tabEl.toggleClass('loading')

                        $.ajax({
                            url: 'detail/', success: function (res) {
                                let { data, success } = res
                                // success
                                if (res && success === 'true') {
                                    // disable button for the next interaction
                                    // unless the form was submitted with success
                                    tabEl.data('triggered', true)
                                    // initialize form here
                                    if (initRoundForm(data)) {
                                        tabEl.toggleClass('loading')
                                        clearTimeout(alertTimer)
                                    } 
                                }
                                // error
                            }
                        })
                    }
                },
            })
    }

    function setAlert(time, type = "warning") {
        return setTimeout(() => {
            alertUser(type, msg="Neco se pokazilo, zkus to znova")
        }, time)
    }

    function orEmpty(val) {
        return val ?? ""
    }

    function createTable(data) {
        const { attackers, defenders, map, winner, mcoms_destroyed } = data;
        let rowsCount = defenders.players.length;
        if (attackers.players.length > defenders.players.length) {
            rowsCount = attackers.players.length
        }
    
        const prezdivka = "Přezdívka"
        const zabiti    = "Zabití"
        const utocnici  = "Útočníci"
        const obranci   = "Obránci"
    
        let rows = Array(rowsCount).fill()
        // row = [Prezdivka, Zabiti, KD, KD+-, KPM, KPM+-, Prezdivka, Zabiti, KD, KD+-, KPM, KPM+-, KPM+-]
        rows = rows.map(function (row, i) {
            // BACHA, na jedne strane muze byt mene hracu nez na druhe
            const attacker = attackers.players[i]
            const defender = defenders.players[i]
    
            const player = (p) => p ? `<td>
            <h4 class="ui image header">
                <img src="${p.user.avatar_url}" class="ui mini rounded image">
                <div class="content">
                    ${p.user.username}
                    <div class="sub header"><i class="${p.role['fa-icon']} icon"></i>${p.role.name}</div>
                </div>
            </h4>
            </td>` : `<td></td>`
    
            return (
                `<tr>
                    ${player(attacker)}
                    <td>
                    ${orEmpty(attacker?.kills)}
                    </td>
                    <td>
                    ${orEmpty(attacker?.kd)}
                    </td>
                    <td>
                    ${orEmpty(attacker?.kd_delta)}
                    </td>
                    <td>
                    ${orEmpty(attacker?.kpm)}
                    </td>
                    <td>
                    ${orEmpty(attacker?.kpm_delta)}
                    </td>
                    <td class="table divider"></td>
                    ${player(defender)}
                    <td>
                        ${orEmpty(defender?.kills)}
                    </td>
                    <td>
                        ${orEmpty(defender?.kd)}
                    </td>
                    <td>
                        ${orEmpty(defender?.kd_delta)}
                    </td>
                    <td>
                        ${orEmpty(defender?.kpm)}
                    </td>
                    <td>
                        ${orEmpty(defender?.kpm_delta)}
                    </td>
                </tr>
            `);
        }).join('')
    
    
        return `
        <table class="ui compact celled table">
            <thead>
                <tr>
                    <th colspan="6" class="utocnik">
                        ${utocnici}
                    </th>
                    <th class="table divider"></th>
                    <th colspan="6" class="obrance">
                        ${obranci}
                    </th>
                </tr>
                <tr>
                    <th>${prezdivka}</th>
                    <th>${zabiti}</th>
                    <th>KD</th>
                    <th>KD +/-</th>
                    <th>KPM</th>
                    <th>KPM +/-</th>
                    <th class="table divider"></th>
                    <th>${prezdivka}</th>
                    <th>${zabiti}</th>
                    <th>KD</th>
                    <th>KD +/-</th>
                    <th>KPM</th>
                    <th>KPM +/-</th>
                </tr>
            </thead>
            <tbody>
                ${rows}
            </tbody>
        </table>
        `;
    }
    
    function initRoundForm(response) {
        // create and render form
        // class="ui bottom attached tab segment" data-tab="add round"
        $FORM_TAB.html(createRoundForm())
        
        const 
            $teamCnt    = (side) => $(`.field[data-team=${side}]`),
            $form       = $('.ui.form'),
            intNotEmpty = ['empty', 'integer'],
            $message    = $('h4 + .ui.message', $form)
        
        // init form fields functionalities
        initDropdowns()
        initGenerateTeamBtn()
        // LISTENER - add player row btn
        $('.ui.form div[name^="addPlayer"]').click(function(e) {
            addPlayerRowHandler(e)
            // when user adds another player, reset team field   
            resetTeamOnChangeHandler(e, team)
        })

        // when user changes leader, reset team field
        $('input[name^="leader"] + .search.dropdown').change(resetTeamOnChangeHandler)

        // when user changes map, change max for mcoms input and its label
        $('select.dropdown.search[data-map]').change(mcomsMaxOnChangeHandler)

        // init form validations and behaviours
        $form.form({
            on: 'submit',
            fields: {
                "order": 'integer[1..]',
                "mapa": 'empty',
                "duration": intNotEmpty,
                "mcomsDestroyed": intNotEmpty,
                "leader[0]": intNotEmpty,
                "leader[1]": intNotEmpty,
            },
            onSuccess: function (event, fields) {
                event.preventDefault()
                const formData = fieldsToJSON(fields),
                      form = $(this)
                if (!hasTeams(formData)) {
                    form.form('add errors', ['Každý tým musí mít alespoň jednoho hráče'])
                    return
                }
                // no issues found
                form.form('remove errors')
                
                form.toggleClass('loading')

                // send data to server application
                $.ajax({
                    method: "POST",
                    url: 'kolo/add/',
                    data: JSON.stringify(formData),
                    contentType: "application/json",
                    headers: {'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value},
                    success: function (res) {
                        let { success } = res
                        // success
                        if (res && success === 'true') {
                            alertUser('success', "Kolo bylo uspesne vytvoreno")
                            return setTimeout(() => {
                                window.location.reload()
                            }, 2000)
                        }
                    },
                    error: function (xhr) {
                        let { message } = JSON.parse(xhr.responseText)
                        // error
                        displayMessage(message)
                    },
                    complete: function (xhr) {
                        setTimeout(() => {
                            form.toggleClass('loading')
                        }, 1000)
                        
                    }
                });
            },
        })
        // initialize draggable sortable
        $( function() {
            $( "#attackers, #defenders" ).sortable({
                connectWith: ".teamPlayers",
                receive: function( event, ui ) {
                    let item = $(ui.item[0]),
                        receiver = item.parent(),
                        sender = $(ui.sender[0])
                    
                    // loop through team container
                    Array(receiver, sender).forEach(function reindexFields(team) {
                        // when received => change in teams => reset both team values
                        resetTeamOnChangeHandler(null, team)
                        
                        const teamIndex = team.data('team')
                        // loop through fields
                        team.children().each(function () {
                            const fieldIndex = $(this).index()
                            // loop through field's inputs
                            // change their names and update form's state
                            // name=value[teamIndex][fieldIndex]
                            $(this).find('input[name]').each(function (i, el) {
                                // remove curr field name from form state
                                $form.form('remove field', el.name)
                                let newName = el.name
                                .replace(PLAYER_REGEX, (m, p1) => (
                                    `${p1}[${teamIndex}][${fieldIndex}]`
                                ))

                                // change field's name
                                el.name = newName
                                // add new field's name into form state
                                $form.form('add field', [newName], intNotEmpty)
                            })

                        })
                    })
                }
            }).disableSelection();
        } );
        
        function displayMessage(msg) {
            let list = [msg].flat().map(m => `<li>${m}</li>`).join("")
            $message.find('ul.list').html(list)
            $message.hasClass('hidden') && $message.removeClass('hidden')
        }

        function mcomsMaxOnChangeHandler(e) {
            // need to wait for the input to be changed
            setTimeout(() => {
                let map		= $(e.target).siblings('input').val()
                let max		= $(e.target).children(`[data-value="${map}"]`).data('mcoms')
                let input = $('input[name="mcomsDestroyed"]')
                // change input max
                input.attr('max', max || 0)
                // change label text
                input.prev().find('.ui.label').text("<=" + (max || "?"))
            }, 100)
        }

        function createRoundForm() {
            let mapOptions = {
                list: response.maps,
                valueField: "map_pk",
                contentField: "name",
                data: ["mcoms"],
                selected: ""
            }
            return (`
                <div class="container" style="max-width: 1024px !important; margin: 0 auto;">
                <form class="ui form">
                    <!-- Round details -->
                    <h4 class="ui dividing header">Údaje o kole</h4>
                    <div class="ui message hidden">
                        <div class="header">Vyskytl se menší problém</div>
                        <ul class="list">
                        </ul>
                    </div>
                    <div class="field">
                    <div class="four fields">
                        <div class="two wide field">
                        <label>Pořadí</label>
                        <input name="order" type="number" min="1" value="${response.rounds_count + 1}">
                        </div>
                        <div class="six wide field">
                        <label>Mapa</label>
                        <input name="mapa" type="hidden" value="">
                        <select class="ui search dropdown" data-map>
                            ${generateOptions(mapOptions)}
                        </select>
                        </div>
                        <div class="four wide field">
                        <label>Doba trvání</label>
                        <input name="duration" type="number" min="1">
                        </div>
                        <div class="four wide field">
                        <label>
                            Zničených MCOM
                            <div class="ui horizontal label">?</div>
                        </label>
                        <input name="mcomsDestroyed" type="number" min="0">
                        </div>
                    </div>
                    </div>
                    <!-- Teams -->
                    <div class="ui two column stackable grid">
                        ${createTeam(0)}
                        ${createTeam(1)}
                    </div>
                    <!-- Submit button -->
                    <h4 class="ui dividing header">Akce</h4>
                    <div class="ui primary submit button">Submit</div>
                    <div class="ui reset button">Reset</div>
                    <div class="ui clear button">Clear</div>
                    <div class="ui error message"></div>
                    </form>
                </div>
            `)
        }

        function createTeam(side) {
            let
            name = side ? "prev_att" : "prev_def"
            next_team = response[name],
            lead = next_team?.leader.player_pk || "",
            team = next_team?.pk || "",
            teamOptions = {
                list: response.teams,
                valueField: "pk",
                contentField: "name",
                selected: team,
            },
            leadOptions = {
                list: response.leaders,
                valueField: "player_pk",
                contentField: "name",
                selected: lead,
            }


            return (`    
                <div class="column" data-team=${side}>
                    <h4 class="ui dividing header">${side ? "Obránci" : "Útočníci"}</h4>
                    <!-- Team details -->
                    <div class="field">
                        <div class="three fields">
                            <div class="seven wide field">
                            <label>Tým</label>
                            <input type="hidden" name="team[${side}]" value="${team}">
                            <select class="ui search dropdown" data-team=${side}>
                                ${generateOptions(teamOptions)}
                            </select>
                            </div>
                            <div class="field">
                            <label style="visibility: hidden;">Akce</label>
                            <div class="ui fluid team button" data-team=${side}>Generuj</div>
                            </div>
                            <div class="seven wide field">
                            <label>Velitel</label>
                            <input type="hidden" name="leader[${side}]" value="${lead}">
                            <select class="ui search dropdown" data-team=${side}>
                                ${generateOptions(leadOptions)}
                            </select>
                            </div>
                        </div>
                    </div>
                    <!-- Players details -->
                    <div class="four fields">
                        <div class="six wide field"><label>Hráč</label></div>
                        <div class="four wide field"><label>Role</label></div>
                        <div class="three wide field"><label>K</label></div>
<div class="three wide field"><label>D</label></div>
                    </div>
                    <div id="${side ? "defenders" : "attackers"}" class="teamPlayers field" data-team=${side}>

                    </div>
                    <!-- Add another player btn -->
                    <div class="ui centered grid">
                    <div class="six wide column">
                        <div class="fluid ui button" name="addPlayer" data-team=${side}>Přidat hráče</div>
                    </div>
                    </div>
                </div>
            `)
        }
    
        function hasTeams(formData) {
            return (
                formData.attackers?.players.length &&
                formData.defenders?.players.length
            )
        }
    
        function addPlayerRowHandler(e, player, index, init = true) {
            const
                f = $form,
                s = $(e.target).data('team'),
                c = $teamCnt(s),
                i = index || c.children().length,
                z = `[${s}][${i}]`,
                p = 'player' + z,
                r = 'role' + z,
                k = 'kills' + z,
                d = 'deaths' + z,
                p_options = {
                    list: response.participants,
                    valueField: "player_pk",
                    contentField: "name",
                },
                r_options = {
                    list: response.roles,
                    valueField: "role_pk",
                    contentField: "name",
                },
                t = (`
                    <div class="four fields ${s ? "defenderOrigin" : "attackerOrigin"}">
                        <div class="six wide field">
                            <input type="hidden" name="${p}" value="${player?.player_pk}">
                            <select class="ui search dropdown" tabindex="-1">
                            ${generateOptions(p_options)}
                            </select>
                        </div>
                        <div class="four wide field">
                            <input type="hidden" name="${r}" value="1">
                            <select class="ui search dropdown" tabindex="-1">
                            ${generateOptions(r_options)}
                            </select>
                        </div>
                        <div class="three wide field">
                            <input type="number" name="${k}" min="0">
                        </div>   
                        <div class="three wide field">
                            <input type="number" name="${d}" min="0">
                        </div>
                    </div>
                `);
    
            c.append(t)
    
    		// add into form's state
            Array(p, r, k, d).forEach(field => {
                f.form('add field', [field], intNotEmpty)
            })
            // if player, automatically fill its select with its value
            player && c.find(`input[name="${p}"] + select`).val(player.player_pk)
            // set role Utocnik with value 1 by default
            c.find(`input[name="${r}"] + select`).val(1)
            // if we add players in batch, don't initialize selects every time
            init && initDropdowns()
    
            return c // return the container it was appended into
        }
        
        function resetTeamOnChangeHandler(e, el) {
        	let 
            target	 = el || $(e.target),
            team     = target.closest('[data-team]').data('team'),
            dropdown = $(`input[name="team[${team}]"] + .dropdown.search`),
            input    = dropdown.siblings('input')
			
            dropdown.val('')
            input.val('')
        }

        function fieldsToJSON(data) {
            const ATT = "attackers",
                DEF = "defenders",
                LDR = "leader"

    
            return Object.keys(data).reduce((o, key) => {
    
                let match, key_name, team, pos
    
                if (PLAYER_REGEX.test(key)) {
                    match       = key.match(PLAYER_REGEX)
                    key_name    = match[1]
                    team        = match[2]
                    pos         = match[3]
    
                } else if (LEADER_REGEX.test(key)) {
                    match       = key.match(LEADER_REGEX)
                    key_name    = match[1]
                    team        = match[2]
                } else {
                    o[key]      = data[key]
                }
    
                team = Number(team) ? DEF : ATT
    
                if (key_name !== LDR) {
                    let cell = o[team].players[pos]
                    if (!cell) {
                        o[team].players[pos] = {}
                    }
                    o[team].players[pos][key_name] = data[key]
                } else {
                    o[team][key_name] = data[key]
                }
    
                return o
            }, {
                attackers: {
                    leader: null,
                    players: [],
                },
                defenders: {
                    leader: null,
                    players: [],
                },
            })
        }
    
        function dropdownHandler(e) {
            let 
                option  = $('option:selected', $(e.target)),
                input   = $(this).parent().find('input[type="hidden"]')
    
            input.val(option.data("value"))
        }
    
        function initDropdowns() {
            $(".ui.search.dropdown").unbind("change", dropdownHandler)
            $(".ui.search.dropdown").bind("change", dropdownHandler)
            // reset team value on player's change
            $('input[name^="player"] + .search.dropdown').unbind('change', resetTeamOnChangeHandler)
            $('input[name^="player"] + .search.dropdown').bind('change', resetTeamOnChangeHandler)
        }
    
        function generateTeamHandler(e) {
            const 
                teamIndex   = $(e.target).data("team"),
                teamPK      = $form.form('get value', `team[${teamIndex}]`)
    
            if (!teamPK) return
    
            const 
                teamContainer   = $teamCnt(teamIndex),
                team            = response.teams.filter(t => t.pk === Number(teamPK))[0],
                leaderInput     = $(`input[name="leader[${teamIndex}]"]`)
    
            leaderInput.val(team.leader.player_pk)
            leaderInput.siblings('.ui.search.dropdown').val(team.leader.player_pk)
    
            teamContainer.empty()
    
            team?.players?.forEach((player, index, t) => {
                addPlayerRowHandler(e, player, index, index === t.length - 1)
            })
        }
    
        function initGenerateTeamBtn() {
            $(".ui.team.button").unbind("click", generateTeamHandler)
            $(".ui.team.button").bind("click", generateTeamHandler)
        }
    
        function generateOptions(o = {
            list: [],
            valueField: "",
            contentField: "",
            data: [],
            selected: ""
        }) {
            let options = '<option value=""> --- </option>'
            o.list.forEach(v => {
                let selected = v[o.valueField] === o.selected ? `selected="selected"` : ""
                let dataset = o.data ? o.data.map(d => `data-${d}="${v[d]}"`).join(" ") : ""
                options += (`
                        <option 
                            value="${v[o.valueField]}" 
                            data-value="${v[o.valueField]}" 
                            ${selected} 
                            ${dataset} 
                        >
                            ${v[o.contentField]}
                        </option>
                        `)
            })
          return options
        }

        return true
    }

    function alertUser(type, msg) {
        $('body')
            .toast({
                class: type,
                message: msg,
                displayTime: 2000,
                showProgress: 'bottom',
                transition: {
                    showMethod: 'scale',
                    showDuration: 500,
                    hideMethod: 'scale',
                    hideDuration: 500,
                    closeEasing: 'easeOutCubic'
                }
            })
    }
})

// for testing

function fillForm() {
    $('[name^=kills]').each(function() {$(this).val(Math.ceil(Math.random() * 100))})
    $('[name^=deaths]').each(function() {$(this).val(Math.ceil(Math.random() * 100))})
    $('[name=duration]').each(function() {$(this).val(Math.ceil(Math.random() * 20) + 10)})
    let $mcoms = $('[name=mcomsDestroyed]')
    let max = Number($mcoms.attr('max'))
    $mcoms.val(Math.floor(Math.random() * (max + 1)))
}