import RetrievalStep from "./RetrievalSteps";

function RetrievalProcess({
    steps
}) {

    if (!steps.length) {
        return null;
    }

    return (

        <section className="retrieval-process">

            <div className="process-header">

                <div>

                    <span className="section-eyebrow">
                        RETRIEVAL PIPELINE
                    </span>

                    <h2>
                        How the search works
                    </h2>

                </div>

            </div>


            <div className="pipeline">

                {steps.map(
                    (step) => (

                        <RetrievalStep
                            key={step.step}
                            step={step}
                        />

                    )
                )}

            </div>

        </section>

    );
}

export default RetrievalProcess;