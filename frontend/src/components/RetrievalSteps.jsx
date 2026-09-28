function RetrievalStep({
    step
}) {

    return (

        <div className="retrieval-step">

            <div className="step-number">
                {step.step}
            </div>


            <div className="step-content">

                <h3>
                    {step.operation}
                </h3>


                <p>
                    {step.description}
                </p>


                <div className="step-details">

                    {step.embedding_dimension && (

                        <span>
                            Dimension:{" "}
                            <strong>
                                {step.embedding_dimension}
                            </strong>
                        </span>

                    )}


                    {step.total_vectors !== undefined && (

                        <span>
                            Vectors:{" "}
                            <strong>
                                {step.total_vectors}
                            </strong>
                        </span>

                    )}


                    {step.requested_results && (

                        <span>
                            Top K:{" "}
                            <strong>
                                {step.requested_results}
                            </strong>
                        </span>

                    )}

                </div>


                {step.formula && (

                    <div className="step-formula">
                        {step.formula}
                    </div>

                )}

            </div>

        </div>

    );
}

export default RetrievalStep;