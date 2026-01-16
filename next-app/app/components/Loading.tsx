import { ThreeDots } from "react-loader-spinner";

export default function Loading({ loading }: { loading: boolean }) {
  return (
    <div className={`mb-3 pb-3 ${loading ? "visible" : "invisible"}`}>
      <ThreeDots
        height={10}
        width={100}
        radius={10}
        color="green"
        ariaLabel="three-dots-loading"
        wrapperStyle={{}}
        wrapperClass=""
      />
    </div>
  );
}
