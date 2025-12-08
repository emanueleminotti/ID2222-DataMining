package se.kth.jabeja;

import se.kth.jabeja.config.Config;
import java.io.IOException;
import java.util.HashMap;

public class SA_Jabeja extends Jabeja {

    public SA_Jabeja(HashMap<Integer, Node> graph, Config config) {
        super(graph, config);
    }

    /**
     * Geometric simulated annealing + restart
     * Overrides the linear cooling from the base class.
     */
    @Override
    protected void saCoolDown() {
        int restartRound = 400;
        if (T > 0.001f)
            T *= config.getDelta(); // Exponential cooling
        else
            T = 0.001f; // Restart mechanism

        if (round > 0 && round % restartRound == 0) {
            T = config.getTemperature();
        }
    }

    /**
     * Overrides the partner selection to use the Task 2 specific probability formula:
     * accept if: newUtility / oldUtility^(1/T) > 1.0
     */
    @Override
    public Node findPartner(int nodeId, Integer[] candidates) {
        Node nodep = entireGraph.get(nodeId);
        Node bestPartner = null;

        double bestUtility = 0;
        // Task 2 uses a fixed alpha of 2.0 as per the provided file
        double alpha = 2.0; 

        for (int qId : candidates) {
            Node nodeq = entireGraph.get(qId);

            // Compute old degrees (existing configuration)
            int d_pp = getDegree(nodep, nodep.getColor());
            int d_qq = getDegree(nodeq, nodeq.getColor());

            // Compute new degrees (hypothetical swap)
            int d_pq = getDegree(nodep, nodeq.getColor());
            int d_qp = getDegree(nodeq, nodep.getColor());

            // Calculate utilities
            double oldUtility = Math.pow(d_pp, alpha) + Math.pow(d_qq, alpha);
            double newUtility = Math.pow(d_pq, alpha) + Math.pow(d_qp, alpha);

            // -------- ACCEPTANCE RULE --------
            boolean accept = Math.exp((newUtility - oldUtility) / T) > Math.random();
            //boolean accept = newUtility / Math.pow(oldUtility, 1.0 / T) > 1.0;

            if (accept && newUtility > bestUtility) {
                bestUtility = newUtility;
                bestPartner = nodeq;
            }
        }
        return bestPartner;
    }
}