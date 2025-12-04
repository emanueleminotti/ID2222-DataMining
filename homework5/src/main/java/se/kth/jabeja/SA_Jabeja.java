package se.kth.jabeja;

import se.kth.jabeja.config.Config;

import java.io.FileWriter;
import java.io.IOException;
import java.util.ArrayList;

public class SA_Jabeja extends Jabeja {

    private double T;  // temperature
    private final double alpha; // cooling rate

    public SA_Jabeja(java.util.HashMap<Integer, Node> graph, Config config) {
        super(graph, config);
        this.T = 1.0;
        this.alpha = config.getAlpha();
    }

    public void startSAJabeja() throws IOException {
        for (round = 0; round < config.getRounds(); round++) {
            for (Node node : entireGraph.values()) {
                findPartnerSA(node);
            }
            saCoolDown();
            report();
        }
    }

    private double acceptanceProbability(double oldCost, double newCost) {
        if (newCost < oldCost)
            return 1.0;
        return Math.exp(-(newCost - oldCost) / T);
    }

    private void findPartnerSA(Node nodep) {
        ArrayList<Node> candidates = getCandidatePartners(nodep);
        Node bestPartner = null;
        double bestProb = 0;
        int pColor = nodep.getColor();
        double oldCost = computeUtility(nodep, pColor);

        for (Node nodeq : candidates) {
            int qColor = nodeq.getColor();
            double newCost = computeUtility(nodep, qColor);
            double ap = acceptanceProbability(oldCost, newCost);

            if (ap > bestProb && Math.random() < ap) {
                bestProb = ap;
                bestPartner = nodeq;
            }
        }

        if (bestPartner != null)
            swapColors(nodep, bestPartner);
    }

    protected void saCoolDown() {
        T = T * alpha;
        if (T < 0.00001)
            T = 0.00001;
    }
}
