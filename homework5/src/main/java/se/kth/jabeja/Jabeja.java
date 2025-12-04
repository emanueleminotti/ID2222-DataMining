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
    protected final HashMap<Integer, Node> entireGraph;
    protected final List<Integer> nodeIds;
    protected int numberOfSwaps;
    protected int round;
    protected float T;
    protected boolean resultFileCreated = false;

    //-------------------------------------------------------------------
    public Jabeja(HashMap<Integer, Node> graph, Config config) {
        this.entireGraph = graph;
        this.nodeIds = new ArrayList<>(entireGraph.keySet());
        this.round = 0;
        this.numberOfSwaps = 0;
        this.config = config;
        this.T = config.getTemperature();
    }

    //-------------------------------------------------------------------
    public void startJabeja() throws IOException {
        for (round = 0; round < config.getRounds(); round++) {
            for (int id : entireGraph.keySet()) {
                sampleAndSwap(id);
            }

            // Reduce temperature
            saCoolDown();
            report();
        }
    }

    protected void saCoolDown() {
        if (T > 1) {
            T -= config.getDelta();
        }
        if (T < 1) {
            T = 1;
        }
    }

    private void sampleAndSwap(int nodeId) {
        Node partner = null;
        Node nodep = entireGraph.get(nodeId);

        if (config.getNodeSelectionPolicy() == NodeSelectionPolicy.HYBRID
                || config.getNodeSelectionPolicy() == NodeSelectionPolicy.LOCAL) {
            partner = findPartner(nodeId, getNeighbors(nodep));
        }

        if (partner == null && (config.getNodeSelectionPolicy() == NodeSelectionPolicy.HYBRID
                || config.getNodeSelectionPolicy() == NodeSelectionPolicy.RANDOM)) {
            partner = findPartner(nodeId, getSample(nodeId));
        }

        if (partner != null) {
            int pColor = nodep.getColor();
            int qColor = partner.getColor();

            nodep.setColor(qColor);
            partner.setColor(pColor);

            numberOfSwaps++;
        }
    }

    public Node findPartner(int nodeId, Integer[] nodes) {
        Node nodep = entireGraph.get(nodeId);

        Node bestPartner = null;
        double highestBenefit = 0;
        double alpha = config.getAlpha();

        for (Integer candidateId : nodes) {
            Node nodeq = entireGraph.get(candidateId);

            int d_pp = getDegree(nodep, nodep.getColor());
            int d_qq = getDegree(nodeq, nodeq.getColor());
            int d_pq = getDegree(nodep, nodeq.getColor());
            int d_qp = getDegree(nodeq, nodep.getColor());

            double oldUtility = Math.pow(d_pp, alpha) + Math.pow(d_qq, alpha);
            double newUtility = Math.pow(d_pq, alpha) + Math.pow(d_qp, alpha);

            double benefit = (newUtility * T) - oldUtility;

            if (benefit > 0 && benefit > highestBenefit) {
                bestPartner = nodeq;
                highestBenefit = benefit;
            }
        }
        return bestPartner;
    }

    protected int getDegree(Node node, int colorId) {
        int degree = 0;
        for (int neighborId : node.getNeighbours()) {
            Node neighbor = entireGraph.get(neighborId);
            if (neighbor.getColor() == colorId) {
                degree++;
            }
        }
        return degree;
    }

    protected Integer[] getSample(int currentNodeId) {
        int count = config.getUniformRandomSampleSize();
        int size = entireGraph.size();
        ArrayList<Integer> rndIds = new ArrayList<>();

        while (count > 0) {
            int rndId = nodeIds.get(RandNoGenerator.nextInt(size));
            if (rndId != currentNodeId && !rndIds.contains(rndId)) {
                rndIds.add(rndId);
                count--;
            }
        }
        return rndIds.toArray(new Integer[0]);
    }

    protected Integer[] getNeighbors(Node node) {
        ArrayList<Integer> list = node.getNeighbours();
        int count = config.getRandomNeighborSampleSize();
        int size = list.size();
        ArrayList<Integer> rndIds = new ArrayList<>();

        if (size <= count)
            rndIds.addAll(list);
        else {
            while (count > 0) {
                int index = RandNoGenerator.nextInt(size);
                int rndId = list.get(index);
                if (!rndIds.contains(rndId)) {
                    rndIds.add(rndId);
                    count--;
                }
            }
        }
        return rndIds.toArray(new Integer[0]);
    }

    protected void report() throws IOException {
        int grayLinks = 0;
        int migrations = 0;
        for (Node node : entireGraph.values()) {
            int nodeColor = node.getColor();
            if (nodeColor != node.getInitColor())
                migrations++;

            for (int n : node.getNeighbours()) {
                Node neighbor = entireGraph.get(n);
                if (neighbor.getColor() != nodeColor)
                    grayLinks++;
            }
        }
        int edgeCut = grayLinks / 2;

        logger.info("round: " + round +
                ", edge cut:" + edgeCut +
                ", swaps: " + numberOfSwaps +
                ", migrations: " + migrations);

        saveToFile(edgeCut, migrations);
    }

    protected void saveToFile(int edgeCuts, int migrations) throws IOException {
        String delimiter = "\t\t";
        String outputFilePath;
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
            if (!outputDir.exists() && !outputDir.mkdir()) {
                throw new IOException("Unable to create the output directory");
            }
            String header = "# Migration is number of nodes that have changed color.";
            header += "\n\nRound" + delimiter + "Edge-Cut" + delimiter + "Swaps" + delimiter + "Migrations" + delimiter + "Skipped" + "\n";
            FileIO.write(header, outputFilePath);
            resultFileCreated = true;
        }
        FileIO.append(round + delimiter + edgeCuts + delimiter + numberOfSwaps + delimiter + migrations + "\n", outputFilePath);
    }

    // --------------------
    // Methods for SA_Jabeja
    // --------------------
    protected double computeUtility(Node node, int color) {
        double d = getDegree(node, color);
        return Math.pow(d, config.getAlpha());
    }

    protected ArrayList<Node> getCandidatePartners(Node nodep) {
        ArrayList<Node> list = new ArrayList<>();
        if (config.getNodeSelectionPolicy() == NodeSelectionPolicy.LOCAL ||
                config.getNodeSelectionPolicy() == NodeSelectionPolicy.HYBRID) {
            for (int n : getNeighbors(nodep))
                list.add(entireGraph.get(n));
        }
        if (config.getNodeSelectionPolicy() == NodeSelectionPolicy.RANDOM ||
                (config.getNodeSelectionPolicy() == NodeSelectionPolicy.HYBRID && list.isEmpty())) {
            for (int n : getSample(nodep.getId()))
                list.add(entireGraph.get(n));
        }
        return list;
    }

    protected void swapColors(Node a, Node b) {
        int ca = a.getColor();
        a.setColor(b.getColor());
        b.setColor(ca);
        numberOfSwaps++;
    }
}