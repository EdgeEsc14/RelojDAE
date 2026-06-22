import { Search, SlidersHorizontal } from "lucide-react";

function SearchFilterBar({ placeholder = "Buscar..." }) {
  return (
    <div className="filters-row">
      <div className="filter-search">
        <Search size={18} />
        <input type="text" placeholder={placeholder} />
      </div>

      <button className="secondary-button" type="button">
        <SlidersHorizontal size={17} />
        Filtros
      </button>
    </div>
  );
}

export default SearchFilterBar;