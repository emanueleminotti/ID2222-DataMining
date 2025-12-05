package se.kth.jabeja;

import org.apache.log4j.Logger;
import se.kth.jabeja.config.Config;
import se.kth.jabeja.config.NodeSelectionPolicy;
import se.kth.jabeja.io.FileIO;
import se.kth.jabeja.rand.RandNoGenerator;

import java.io.File;
import java.io.IOException;
import java.util.*;
public class SA_Jabeja extends Jabeja {

    private double T; 
    private double alpha; // delta in the context of exponential cooling

    public SA_Jabeja(HashMap<Integer, Node> graph, Config config) {
        super(graph, config);
        this.T = 1.0;
        this.alpha = config.getDelta(); // Ensure config.getDelta() returns the cooling rate (e.g., 0.9, 0.99)
    }

    @Override
    public void startJabeja() throws IOException {
        for (round = 0; round < config.getRounds(); round++) {
            for (Integer nodeId : entireGraph.keySet()) {
                sampleAndSwap(nodeId);
            }
            saCoolDown();
            report();
        }
    }

    public void saCoolDown() {
        // Exponential cooling: T = T * alpha
        if (T > 0.00001) {
            T *= alpha;
        }
        
        // TODO for Part 2: Add Restart Logic here
        // if (round % 400 == 0) T = 1.0;
    }

    /**
     * Override or create a new version of sampleAndSwap/findPartner 
     * that uses the Metropolis-Hastings criterion.
     */
    private void sampleAndSwap(int nodeId) {
        Node nodep = entireGraph.get(nodeId);
        Integer[] neighbors = getNeighbors(nodep); // Or getSample(nodeId) based on policy
        
        // 1. Find the BEST partner first
        Node bestPartner = null;
        double maxDiff = -Double.MAX_VALUE;

        for (Integer neighborId : neighbors) {
            Node nodeq = entireGraph.get(neighborId);
            
            int d_pp = getDegree(nodep, nodep.getColor());
            int d_qq = getDegree(nodeq, nodeq.getColor());
            int d_pq = getDegree(nodep, nodeq.getColor());
            int d_qp = getDegree(nodeq, nodep.getColor());
            
            double oldUtility = Math.pow(d_pp, config.getAlpha()) + Math.pow(d_qq, config.getAlpha());
            double newUtility = Math.pow(d_pq, config.getAlpha()) + Math.pow(d_qp, config.getAlpha());
            
            double diff = newUtility - oldUtility;
            
            // Keep track of the partner that gives the highest utility gain (or lowest loss)
            if (diff > maxDiff) {
                maxDiff = diff;
                bestPartner = nodeq;
            }
        }

        // 2. Apply Acceptance Probability to the BEST partner found
        if (bestPartner != null) {
            boolean accept = false;
            if (maxDiff > 0) {
                // Always accept improvement
                accept = true;
            } else {
                // Accept bad moves with probability exp(diff / T)
                // Note: diff is negative here, so the result is between 0 and 1
                double probability = Math.exp(maxDiff / T);
                if (Math.random() < probability) {
                    accept = true;
                }
            }

            if (accept) {
                // Perform Swap
                int pColor = nodep.getColor();
                int qColor = bestPartner.getColor();
                nodep.setColor(qColor);
                bestPartner.setColor(pColor);
                // numberOfSwaps++; // If you have access to this counter
            }
        }
    }
}
