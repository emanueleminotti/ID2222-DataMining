package se.kth.jabeja;

import org.apache.log4j.Logger;
import se.kth.jabeja.config.Config;
import se.kth.jabeja.config.NodeSelectionPolicy;
import se.kth.jabeja.io.FileIO;
import se.kth.jabeja.rand.RandNoGenerator;

import java.io.File;
import java.io.IOException;
import java.util.*;

public class Jabeja {
    final static Logger logger = Logger.getLogger(Jabeja.class);
    protected final Config config;
    protected final HashMap<Integer/*id*/, Node/*neighbors*/> entireGraph;
    private final List<Integer> nodeIds;
    private int numberOfSwaps;
    protected int round;
    protected float T;
    private boolean resultFileCreated = false;

    //-------------------------------------------------------------------
    public Jabeja(HashMap<Integer, Node> graph, Config config) {
        this.entireGraph = graph;
        this.nodeIds = new ArrayList(entireGraph.keySet());
        this.round = 0;
        this.numberOfSwaps = 0;
        this.config = config;
        this.T = config.getTemperature();
    }


    //-------------------------------------------------------------------
    public void startJabeja() throws IOException {
        // 1. Timer Start
        long startTime = System.currentTimeMillis();
        
        int minEdgeCut = Integer.MAX_VALUE;
        int convergenceRound = 0;
        int totalSwaps = 0; // Se numberOfSwaps viene resettato, usane uno cumulativo

        for (round = 0; round < config.getRounds(); round++) {
            for (int id : entireGraph.keySet()) {
                sampleAndSwap(id);
            }

            //one cycle for all nodes have completed.
            //reduce the temperature
            saCoolDown();
            
            // --- LOGICA DI REPORTING AGGIUNTA ---
            // Calcoliamo l'edge cut corrente (copiato dalla funzione report)
            int grayLinks = 0;
            for (int i : entireGraph.keySet()) {
                Node node = entireGraph.get(i);
                int nodeColor = node.getColor();
                if (node.getNeighbours() != null) {
                    for (int n : node.getNeighbours()) {
                        Node p = entireGraph.get(n);
                        if (nodeColor != p.getColor()) grayLinks++;
                    }
                }
            }
            int currentEdgeCut = grayLinks / 2;

            // Aggiorna il minimo e il round di convergenza
            if (currentEdgeCut < minEdgeCut) {
                minEdgeCut = currentEdgeCut;
                convergenceRound = round;
            }
            // ------------------------------------

            report();
        }

        // 2. Timer End
        long endTime = System.currentTimeMillis();
        long duration = endTime - startTime;

        // 3. STAMPA FINALE DELLE METRICHE PER IL REPORT
        System.out.println("\n##################################################");
        System.out.println("FINAL METRICS FOR REPORT");
        System.out.println("##################################################");
        System.out.println("Graph: " + config.getGraphFilePath());
        System.out.println("Policy: " + config.getNodeSelectionPolicy());
        System.out.println("Min Edge Cut: " + minEdgeCut);
        System.out.println("Convergence Round (Best Solution found): " + convergenceRound);
        System.out.println("Total Swaps: " + numberOfSwaps);
        System.out.println("Execution Time (ms): " + duration);
        System.out.println("Execution Time (sec): " + (duration / 1000.0));
        System.out.println("##################################################\n");
    }

    /**
     * Simulated annealing cooling function
     * Implements linear cooling: T_r = max(1, T_{r-1} - delta) 
     */
    protected void saCoolDown(){
        if (T > 1)
            T -= config.getDelta();
        if (T < 1)
            T = 1;
    }

    /**
     * Sample and swap algorithm at node p
     * Implements Algorithm 1 and the Hybrid policy
     * @param nodeId
     */
    private void sampleAndSwap(int nodeId) {
        Node partner = null;
        Node nodep = entireGraph.get(nodeId);

        if (config.getNodeSelectionPolicy() == NodeSelectionPolicy.HYBRID
                || config.getNodeSelectionPolicy() == NodeSelectionPolicy.LOCAL) {
        // Local Policy: Try to find a partner among immediate neighbors
        partner = findPartner(nodeId, getNeighbors(nodep));
        }

        if (config.getNodeSelectionPolicy() == NodeSelectionPolicy.HYBRID
                || config.getNodeSelectionPolicy() == NodeSelectionPolicy.RANDOM) {
        // Hybrid/Random Policy: If local failed (partner is null), try random sample
        if (partner == null) {
            partner = findPartner(nodeId, getSample(nodeId));
        }
        }

        // swap the colors if a suitable partner was found
        if (partner != null) {
        int pColor = nodep.getColor();
        int qColor = partner.getColor();
        nodep.setColor(qColor);
        partner.setColor(pColor);
        numberOfSwaps++;
        }
    }

    /**
     * Finds the best partner from a set of candidates based on Equation 10.
     * @param nodeId The ID of the node initiating the swap (node p).
     * @param nodes The array of candidate node IDs (neighbors or random sample).
     * @return The best partner node, or null if no swap yields positive utility.
     */
    public Node findPartner(int nodeId, Integer[] nodes){

        Node nodep = entireGraph.get(nodeId);

        Node bestPartner = null;
        double highestUtility = 0;
        double alpha = config.getAlpha();

        for (Integer rId : nodes) {
        Node nodeq = entireGraph.get(rId);

        // Calculate degrees required for Equation 10 
        // d_p(\pi_p): Degree of p with same color as p
        int d_pp = getDegree(nodep, nodep.getColor());
        // d_q(\pi_q): Degree of q with same color as q
        int d_qq = getDegree(nodeq, nodeq.getColor());
        // d_p(\pi_q): Degree of p with same color as q (potential new color)
        int d_pq = getDegree(nodep, nodeq.getColor());
        // d_q(\pi_p): Degree of q with same color as p (potential new color)
        int d_qp = getDegree(nodeq, nodep.getColor());

        // Old energy state: d_p(\pi_p)^\alpha + d_q(\pi_q)^\alpha
        double oldEnergy = Math.pow(d_pp, alpha) + Math.pow(d_qq, alpha);

        // New energy state: d_p(\pi_q)^\alpha + d_q(\pi_p)^\alpha
        double newEnergy = Math.pow(d_pq, alpha) + Math.pow(d_qp, alpha);

        // Calculate Utility using Equation 10: U = (NewEnergy * T) - OldEnergy 
        // We perform the swap if U > 0 and it is the highest found so far.
        double utility = (newEnergy * T) - oldEnergy;

        if (utility > highestUtility) {
            bestPartner = nodeq;
            highestUtility = utility;
        }
        }

        return bestPartner;
    }

    /**
     * The the degree on the node based on color
     * @param node
     * @param colorId
     * @return how many neighbors of the node have color == colorId
     */
    protected int getDegree(Node node, int colorId){
        int degree = 0;
        for(int neighborId : node.getNeighbours()){
        Node neighbor = entireGraph.get(neighborId);
        if(neighbor.getColor() == colorId){
            degree++;
        }
        }
        return degree;
    }

    /**
     * Returns a uniformly random sample of the graph
     * @param currentNodeId
     * @return Returns a uniformly random sample of the graph
     */
    private Integer[] getSample(int currentNodeId) {
        int count = config.getUniformRandomSampleSize();
        int rndId;
        int size = entireGraph.size();
        ArrayList<Integer> rndIds = new ArrayList<Integer>();

        while (true) {
        rndId = nodeIds.get(RandNoGenerator.nextInt(size));
        if (rndId != currentNodeId && !rndIds.contains(rndId)) {
            rndIds.add(rndId);
            count--;
        }

        if (count == 0)
            break;
        }

        Integer[] ids = new Integer[rndIds.size()];
        return rndIds.toArray(ids);
    }

    /**
     * Get random neighbors. The number of random neighbors is controlled using
     * -closeByNeighbors command line argument which can be obtained from the config
     * using {@link Config#getRandomNeighborSampleSize()}
     * @param node
     * @return
     */
    private Integer[] getNeighbors(Node node) {
        ArrayList<Integer> list = node.getNeighbours();
        int count = config.getRandomNeighborSampleSize();
        int rndId;
        int index;
        int size = list.size();
        ArrayList<Integer> rndIds = new ArrayList<Integer>();

        if (size <= count)
        rndIds.addAll(list);
        else {
        while (true) {
            index = RandNoGenerator.nextInt(size);
            rndId = list.get(index);
            if (!rndIds.contains(rndId)) {
            rndIds.add(rndId);
            count--;
            }

            if (count == 0)
            break;
        }
        }

        Integer[] arr = new Integer[rndIds.size()];
        return rndIds.toArray(arr);
    }


    /**
     * Generate a report which is stored in a file in the output dir.
     *
     * @throws IOException
     */
    private void report() throws IOException {
        int grayLinks = 0;
        int migrations = 0; // number of nodes that have changed the initial color
        int size = entireGraph.size();

        for (int i : entireGraph.keySet()) {
        Node node = entireGraph.get(i);
        int nodeColor = node.getColor();
        ArrayList<Integer> nodeNeighbours = node.getNeighbours();

        if (nodeColor != node.getInitColor()) {
            migrations++;
        }

        if (nodeNeighbours != null) {
            for (int n : nodeNeighbours) {
            Node p = entireGraph.get(n);
            int pColor = p.getColor();

            if (nodeColor != pColor)
                grayLinks++;
            }
        }
        }

        int edgeCut = grayLinks / 2;

        logger.info("round: " + round +
                ", edge cut:" + edgeCut +
                ", swaps: " + numberOfSwaps +
                ", migrations: " + migrations);

        saveToFile(edgeCut, migrations);
    }

    private void saveToFile(int edgeCuts, int migrations) throws IOException {
        String delimiter = "\t\t";
        String outputFilePath;

        //output file name
        File inputFile = new File(config.getGraphFilePath());
        outputFilePath = config.getOutputDir() +
                File.separator +
                inputFile.getName() + "_" +
                "NS" + "_" + config.getNodeSelectionPolicy() + "_" +
                "GICP" + "_" + config.getGraphInitialColorPolicy() + "_" +
                "T" + "_" + config.getTemperature() + "_" +
                "D" + "_" + config.getDelta() + "_" +
                "RNSS" + "_" + config.getRandomNeighborSampleSize() + "_" +
                "URSS" + "_" + config.getUniformRandomSampleSize() + "_" +
                "A" + "_" + config.getAlpha() + "_" +
                "R" + "_" + config.getRounds() + ".txt";

        if (!resultFileCreated) {
        File outputDir = new File(config.getOutputDir());
        if (!outputDir.exists()) {
            if (!outputDir.mkdir()) {
            throw new IOException("Unable to create the output directory");
            }
        }
        // create folder and result file with header
        String header = "# Migration is number of nodes that have changed color.";
        header += "\n\nRound" + delimiter + "Edge-Cut" + delimiter + "Swaps" + delimiter + "Migrations" + delimiter + "Skipped" + "\n";
        FileIO.write(header, outputFilePath);
        resultFileCreated = true;
        }

        FileIO.append(round + delimiter + (edgeCuts) + delimiter + numberOfSwaps + delimiter + migrations + "\n", outputFilePath);
    }
}