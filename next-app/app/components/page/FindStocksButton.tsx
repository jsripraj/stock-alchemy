export default function FindStocksButton({
  findStocksClicked,
}: {
  findStocksClicked: () => void;
}) {

  return (
    <div className="flex-1 flex flex-col items-center">
      <button
        className="m-3 p-3 bg-lime-700 border border-lime-500 rounded text-3xl hover:bg-lime-900 cursor-pointer text-lime-50 hover:font-semibold"
        onClick={findStocksClicked}
      >
        Find Stocks &#129122;
      </button>
    </div>
  );
}
