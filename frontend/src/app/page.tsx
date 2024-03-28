import {
  BoltIcon,
  ExclamationTriangleIcon,
  SunIcon,
} from "@heroicons/react/24/outline";

function HomePage() {
  return (
    <div className="flex flex-col items-center justify-center h-screen px-2 text-white">
      <h1 className="text-5xl font-bold mb-20">ChatGPT</h1>
      <div className="flex space-x-2 text-center">
        <div>
          <div className="flex flex-col items-center justify-center mb-5">
            <SunIcon className="h8 w-8" />
            <h2> Examples </h2>
          </div>
          <div className="space-y-2">
            <p className="infoText"> "Explain something to me"</p>
            <p className="infoText"> "What is your name" </p>
            <p className="infoText"> "How are you" </p>
          </div>
        </div>
        <div>
          <div className="flex flex-col items-center justify-center mb-5">
            <BoltIcon className="h8 w-8" />
            <h2> Capabilities </h2>
          </div>
          <div className="space-y-2">
            <p className="infoText"> "Flexible model selection"</p>
            <p className="infoText">
              {" "}
              "Multi-tenent user & api-key management"{" "}
            </p>
            <p className="infoText">
              {" "}
              "Rquest Throttler and API Rate-limiter"{" "}
            </p>
          </div>
        </div>
        <div>
          <div className="flex flex-col items-center justify-center mb-5">
            <ExclamationTriangleIcon className="h8 w-8" />
            <h2> Limitations </h2>
          </div>
          <div className="space-y-2">
            <p className="infoText">
              {" "}
              "Limited GPT platform and LLM models are currently supported"
            </p>
            <p className="infoText">
              {" "}
              "Rate-limiter might be inconsistent for user who are limited by
              the GPT platforms"{" "}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default HomePage;
