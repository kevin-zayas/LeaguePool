// Declare a global variable to store the champion lists
var championListsCache = {};
var championList = []; // Array to store the available champions
var suggestedChampionPools = [];

function handleRoleSelection() {
  var roleSelect = document.getElementById("role-select");
  var selectedRole = roleSelect.value;

  // Check if the selected role is "Select a Role"
  var saveButton = document.getElementById("save-button");
  saveButton.disabled = selectedRole === "";

  // Hide the champion select sections when a new role is selected
  var championPoolSection = document.getElementById("champion-pool-section");
  championPoolSection.style.display = "none";
  var excludedChampionSection = document.getElementById("excluded-champions-section");
  excludedChampionSection.style.display = "none";
  var calculatePoolSection = document.getElementById("calculate-champion-pool-button");
  calculatePoolSection.style.display = "none";

}

function handleRoleSave() {
  var roleSelect = document.getElementById("role-select");
  var selectedRole = roleSelect.value;

  // Check if the champion list for the role is already cached
  if (championListsCache[selectedRole]) {
    championList = championListsCache[selectedRole];
    console.log("Champion List (from cache):", championList);
    showChampionSections();
  } else {
    //url based on the ip of the ec2 instance
    var apiUrl = 'http://3.145.60.140:5000/champion-list?role=' + selectedRole;
    fetch(apiUrl)
      .then(response => response.json())
      .then(responseData => {
        championList = responseData.champion_list.sort();
        championListsCache[selectedRole] = championList;
        console.log("Champion List (from API):", championList);
        showChampionSections();
      })
      .catch(error => {
        console.error("Error:", error);
      });
  }
}

function showChampionSections() {
  var championPoolSection = document.getElementById("champion-pool-section");
  championPoolSection.style.display = "block";
  var excludedChampionSection = document.getElementById("excluded-champions-section");
  excludedChampionSection.style.display = "block";
  var calculatePoolSection = document.getElementById("calculate-champion-pool-button");
  calculatePoolSection.style.display = "block";
  populateSections();
}

function populateDrowpdownSections(section, selectId, buttonId, handler) {
  var container = document.getElementById(section);
  container.innerHTML = "";

  var addButton = document.createElement("button");
  addButton.id = buttonId;
  addButton.textContent = buttonId === "add-champ-button" ? "Add to Pool" : "Exclude Champion";
  addButton.onclick = handler;
  addButton.disabled = true;

  var select = document.createElement("select");
  select.id = selectId;
  select.onchange = function () {
    handleChampSelection(select, addButton);
  };

  container.appendChild(select);
  container.appendChild(addButton);

  var defaultOption = document.createElement("option");
  defaultOption.value = "";
  defaultOption.textContent = "Select a Champion";
  select.appendChild(defaultOption);

  // Populate the champion select dropdown
  for (var i = 0; i < championList.length; i++) {
    var option = document.createElement("option");
    option.value = championList[i];
    option.textContent = championList[i];
    select.appendChild(option);
  }
}

function populateSections() {
  populateDrowpdownSections("champion-pool", "champion-select-add", "add-champ-button", addChampionToPool);
  populateDrowpdownSections("excluded-champions", "champion-select-exclude", "exclude-champ-button", excludeChampion);
}

function handleChampSelection(select, button) {
  var selectedChampion = select.value;
  button.disabled = selectedChampion === "" ? true : false;
}

function addChampionToPool() {
  var championSelect = document.getElementById("champion-select-add");
  var selectedChampion = championSelect.value;

  var championPoolList = document.getElementById("champion-pool-list") || createList("champion-pool");
  var championPoolItem = createChampionItem(selectedChampion, championPoolList, "add-champ-button");

  championPoolList.appendChild(championPoolItem);

  // Remove the selected champion option from the dropdown
  removeChampionOption(selectedChampion);

  var addChampButton = document.getElementById("add-champ-button");
  addChampButton.disabled = true;
}

function excludeChampion() {
  var championSelect = document.getElementById("champion-select-exclude");
  var selectedChampion = championSelect.value;

  var excludedChampionList = document.getElementById("excluded-champions-list") || createList("excluded-champions");
  var excludedChampionItem = createChampionItem(selectedChampion, excludedChampionList, "exclude-champ-button");

  excludedChampionList.appendChild(excludedChampionItem);

  // Remove the selected champion option from the dropdown
  removeChampionOption(selectedChampion);

  var excludeChampionButton = document.getElementById("exclude-champ-button");
  excludeChampionButton.disabled = true;
}

function createList(id) {
  var container = document.getElementById(id);
  var list = document.createElement("ul");
  list.id = id + "-list";
  container.appendChild(list);
  return list;
}

function createChampionItem(championName, list, buttonId) {
  var item = document.createElement("li");
  item.className = buttonId === "add-champ-button" ? "champion-pool-item" : "excluded-champion-item";

  var championNameSpan = document.createElement("span");
  championNameSpan.className = "champion-name";
  championNameSpan.textContent = championName;

  var removeButton = document.createElement("button");
  removeButton.className = "remove-icon";
  removeButton.setAttribute("aria-label", "Remove Champion");
  removeButton.onclick = function () {
    removeChampionFromList(list, item);
  };

  item.appendChild(championNameSpan);
  item.appendChild(removeButton);

  return item;
}

function removeChampionFromList(list, item) {
  list.removeChild(item);

  var championName = item.firstChild.textContent;
  var championSelectAdd = document.getElementById("champion-select-add");
  var championSelectExclude = document.getElementById("champion-select-exclude");

  var option = document.createElement("option");
  option.value = championName;
  option.textContent = championName;

  championSelectAdd.appendChild(option.cloneNode(true));
  championSelectExclude.appendChild(option);

  // Sort the options in both dropdown menus
  sortDropdownOptions(championSelectAdd);
  sortDropdownOptions(championSelectExclude);
}

function sortDropdownOptions(select) {
  var options = Array.from(select.options);

  options.sort((a, b) => {
    if (a.value === "") {
      return -1; // "Select a champion" should come before other options
    } else if (b.value === "") {
      return 1; // "Select a champion" should come before other options
    } else {
      return a.textContent.localeCompare(b.textContent);
    }
  });

  select.innerHTML = "";

  options.forEach(option => select.appendChild(option));
}

function removeChampionOption(selectedChampion) {
  var championSelectAdd = document.getElementById("champion-select-add");
  var championSelectExclude = document.getElementById("champion-select-exclude");

  var optionToRemove = championSelectAdd.querySelector('option[value="' + selectedChampion + '"]');
  if (optionToRemove) {
    optionToRemove.remove();
  }

  optionToRemove = championSelectExclude.querySelector('option[value="' + selectedChampion + '"]');
  if (optionToRemove) {
    optionToRemove.remove();
  }
}

function caclulateChampPools(){
  var currentPoolString;
  var excludedChampsString;

  var championPoolList = document.getElementById("champion-pool-list");
  if (championPoolList){
    currentPoolString = Array.from(championPoolList.children).map(function(item) {
      return item.firstChild.textContent;
    }).join(",");;
  } else {
    currentPoolString = ""
  }


  var excludedChampionList = document.getElementById("excluded-champions-list")
  if (excludedChampionList){
    excludedChampsString = Array.from(excludedChampionList.children).map(function(item) {
      return item.firstChild.textContent;
    }).join(",");
  } else{
    excludedChampsString = ""
  }



  //http://3.144.102.47:5000/champion-pool?current_champions=illaoi,garen&exclude_champions=kayle
  //url based on the ip of the ec2 instance
  var apiUrl = 'http://3.145.60.140:5000/champion-pool?current_champions='+currentPoolString+'&exclude_champions=' + excludedChampsString;
  console.log("URL: ", apiUrl)
  fetch(apiUrl)
    .then(response => response.json())
    .then(responseData => {
      suggestedChampionPools = responseData.champion_pools;
      console.log("Champion List (from API):", suggestedChampionPools);

      var suggestedChampionsContainer = document.getElementById("suggested-champions");
      suggestedChampionsContainer.style.display = "block";
      var suggestedChampionsList = document.getElementById("suggested-champions-list") || createList("suggested-champions");

      var item = document.createElement("li");
      item.className = "suggested-champion-item";

      var suggestedPoolSpan = document.createElement("span");
      suggestedPoolSpan.className = "suggested-pool";
      console.log("pool: ",suggestedChampionPools.join(", "));
      suggestedPoolSpan.textContent = suggestedChampionPools.join(", ");

      item.appendChild(suggestedPoolSpan);
      suggestedChampionsList.appendChild(item)
    })
    .catch(error => {
      console.error("Error:", error);
    });


}
