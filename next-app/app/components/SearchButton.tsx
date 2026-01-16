export default function SearchButton({
  searchClicked,
}: {
  searchClicked: () => void;
}) {
  return (
    <div className="flex-1 flex flex-col items-center max-h-fit">
      <button
        id="find-stocks-btn"
        className="m-3 p-3 bg-lime-700 border border-lime-500 rounded text-3xl hover:bg-lime-900 cursor-pointer text-lime-50 hover:font-semibold"
        onClick={searchClicked}
      >
        {"Search >"}
      </button>
    </div>
  );
}
